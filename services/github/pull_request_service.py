import logging
import re
import sqlite3
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

from libs import llmFactory, modeltypeenums
from libs.github import repo
from libs.prompt_templates.code_diff_summary import code_diff_summary_parser, code_diff_summary_prompt
from libs.sqlite.core.core_sqlite_client import Database
from models.models import CodeDiffSummary, FilePatch, PullRequest

logger = logging.getLogger(__name__)


def _get_pull_requests_between(base: str, head: str) -> list[int] | None:
    comparison = repo.compare(base=base, head=head)

    pr_numbers = set()
    for commit in comparison.commits:
        match = re.search(r"Merge pull request #(\d+)", commit.commit.message)
        if match:
            pr_numbers.add(int(match.group(1)))

    return sorted(list(pr_numbers)) if pr_numbers else None


def add_new_pull_requests_between(base: str, head: str, issue_id: int, db: Database) -> None:
    new_ids = _get_pull_requests_between(base, head)
    if not new_ids:
        return

    logging.info(f"{issue_id}: found {len(new_ids)} new pull requests {new_ids}")
    existing_ids = db.get_existing_pr_ids()
    new_ids_to_process = [pr_id for pr_id in new_ids if pr_id not in existing_ids]
    logging.info(f"{issue_id}: processing {len(new_ids_to_process)} new pull requests")

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(_get_pr_with_embeddings, pr_id): pr_id for pr_id in new_ids_to_process}
        for future in as_completed(futures):
            pull_request = future.result()
            if pull_request:
                db.add_pull_request(pull_request)

    # link all pull requests to the issue, even if they are not new
    for pr_id in new_ids:
        try:
            db.add_issue_pull_request(issue_id, pr_id)
        except sqlite3.IntegrityError as e:
            logging.warning(f"#{issue_id} failed to add issue pull request - {pr_id}: {e}")


def _get_code_diff(diff_url: str) -> str:
    try:
        headers = {"Accept": "application/vnd.github.v3.diff"}
        response = requests.get(diff_url, headers=headers, timeout=30)
        if response.status_code != 200:
            logging.error(f"failed to fetch diff from {diff_url}: {response.status_code}")
            return ""

        diff_text = response.text

        kept_lines = []
        keep = False
        file_header_re = re.compile(r"^diff --git a/(.*?) b/")
        for line in diff_text.splitlines(keepends=True):
            m = file_header_re.match(line)
            if m:
                keep = m.group(1).startswith("src/") and not m.group(1).startswith("src/languages")
            if keep:
                kept_lines.append(line)

        filtered_diff = "".join(kept_lines)
        return filtered_diff.strip() if filtered_diff else ""
    except Exception as e:
        logging.error(f"failed to fetch code diff from {diff_url}: {e}")
        return ""


def _get_pr_with_embeddings(pull_request_id: int) -> PullRequest | None:
    try:
        pr = repo.get_pull(pull_request_id)
        all_files = pr.get_files()

        files = [f.filename for f in all_files]

        pr_test = _parse_test_steps(pr.body or "")
        pr_explaination = _parse_explaination(pr.body or "")

        code_diff = _get_code_diff(pr.diff_url)
        code_diff_summary_input = code_diff_summary_prompt.format(
            title=pr.title,
            test=pr_test,
            explanation=pr_explaination,
            code_diff=code_diff,
        )
        llmReasoningCheap = llmFactory.llmFactory().getLLM(
            "open-ai",
            False,
            modelType=modeltypeenums.ModelThinkingType.REASONING,
            cost=modeltypeenums.ModelCostType.CHEAP,
        )
        response = llmReasoningCheap.invoke(code_diff_summary_input)
        code_diff_summary = code_diff_summary_parser.invoke(response)
        assert isinstance(code_diff_summary, CodeDiffSummary), "code diff summary parsing failed"

        pr_text = f"Title: {pr.title}\n Tests: {pr_test}\n Explaination: {pr_explaination}\n Files changed: {files}\n Code diff summary: {code_diff_summary.pull_request_description}"
        embedding_model = llmFactory.llmFactory().getLLM(
            "open-ai",
            False,
            modelType=modeltypeenums.ModelThinkingType.EMBEDDING,
            cost=modeltypeenums.ModelCostType.STANDARD,
        )
        pr_embedding = embedding_model.embed_query(pr_text)

        return PullRequest(
            id=pr.number,
            title=pr.title,
            test=pr_test,
            explaination=pr_explaination,
            files=files,
            embedding=pr_embedding,
            code_diff_summary=code_diff_summary.pull_request_description,
        )
    except Exception as e:
        logging.error(f"failed to process PR {pull_request_id}: {e}")
        return None


def _parse_test_steps(body: str) -> str:
    pattern = r"(### Tests.*?)(?=### PR Author Checklist)"
    match = re.search(pattern, body, re.DOTALL | re.IGNORECASE)
    if not match:
        return ""

    raw_section = match.group(1).strip()
    unified_newlines = raw_section.replace("\r\n", "\n").replace("\r", "\n")
    without_checkboxes = re.sub(r"- \[[ xX]\]\s*", "", unified_newlines)
    without_comments = re.sub(r"<!--.*?-->", "", without_checkboxes, flags=re.DOTALL)
    normalized_spacing = re.sub(r"\n{3,}", "\n\n", without_comments)

    return normalized_spacing.strip()


def _parse_explaination(body: str) -> str:
    pattern = r"### Explanation of Change(.*?)### Fixed Issues"
    match = re.search(pattern, body, re.DOTALL | re.IGNORECASE)
    if not match:
        return ""

    raw_section = match.group(1).strip()
    without_comments = re.sub(r"<!--.*?-->", "", raw_section, flags=re.DOTALL)
    normalized_spacing = re.sub(r"\n{3,}", "\n\n", without_comments)

    return normalized_spacing.strip()


def get_pull_request_patch(pull_request_id: int) -> list[FilePatch]:
    patches: list[FilePatch] = []

    pr = repo.get_pull(pull_request_id)
    for file in pr.get_files():
        if not file.patch:
            continue

        patches.append(
            FilePatch(
                filename=file.filename,
                patch=file.patch or "",
            )
        )
    return patches


def add_pull_request(pull_request_id: int, db: Database) -> PullRequest | None:
    existing_pr = db.get_pull_request_by_id_with_embedding(pull_request_id)
    if existing_pr:
        return existing_pr

    pull_request = _get_pr_with_embeddings(pull_request_id)
    if not pull_request:
        logging.error(f"failed to fetch pull request {pull_request_id}")
        return None

    db.add_pull_request(pull_request)
    return pull_request
