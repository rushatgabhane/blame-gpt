import logging
import re
import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

import pathspec
import requests
from github.Repository import Repository

from libs.constants import SIGNATURE
from libs.helpers import is_production_environment
from libs.llm import ModelNames, embedding_model, llm
from libs.prompt_templates.code_diff_summary import code_diff_summary_parser, code_diff_summary_prompt
from libs.sqlite.core.core_sqlite_client import Database
from models.models import CodeDiffSummary, LineByLineCodeReview, PRFileDiff, PullRequest
from services.review_service import is_allowed_comment_type
from services.user_service import track_llm_usage

logger = logging.getLogger(__name__)
_add_new_prs_lock = threading.Lock()


def _get_pull_requests_between(base: str, head: str, repo_client: Repository) -> list[int] | None:
    comparison = repo_client.compare(base=base, head=head)

    pr_numbers = set()
    for commit in comparison.commits:
        # Ignores reverted PRs by design
        match = re.search(r"^Merge pull request #(\d+)", commit.commit.message)
        if match:
            pr_numbers.add(int(match.group(1)))

    return sorted(list(pr_numbers)) if pr_numbers else None


def add_new_pull_requests_between(
    base: str,
    head: str,
    issue_id: int,
    repo_id: int,
    repo_client: Repository,
    db: Database,
    usage_log_id: int | None = None,
) -> None:
    with _add_new_prs_lock:
        new_ids = _get_pull_requests_between(base, head, repo_client)
        if not new_ids:
            return

        logging.info(f"{issue_id}: found {len(new_ids)} new pull requests {new_ids}")
        existing_ids = db.get_existing_pr_ids(repo_id)
        new_ids_to_process = [pr_id for pr_id in new_ids if pr_id not in existing_ids]
        logging.info(f"{issue_id}: processing {len(new_ids_to_process)} new pull requests")

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {
                executor.submit(_get_pr_with_embeddings, pr_id, repo_client, db, usage_log_id): pr_id
                for pr_id in new_ids_to_process
            }
            for future in as_completed(futures):
                pull_request = future.result()
                if pull_request:
                    db.add_pull_request(pull_request, repo_id)

        # link all pull requests to the issue, even if they are not new
        for pr_id in new_ids:
            try:
                db.add_issue_pull_request(issue_id, pr_id, repo_id)
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


def _get_pr_with_embeddings(
    pull_request_id: int, repo_client: Repository, db: Database, usage_log_id: int | None = None
) -> PullRequest | None:
    try:
        pr = repo_client.get_pull(pull_request_id)
        all_files = pr.get_files()

        files = [f.filename for f in all_files]

        pr_test = _parse_test_steps(pr.body or "")
        linked_issue_ids = _parse_linked_issue_ids(pr.body or "", repo_client.name)
        pr_explanation = _parse_explanation(pr.body or "")

        code_diff = _get_code_diff(pr.diff_url)
        code_diff_summary_input = code_diff_summary_prompt.format(
            title=pr.title,
            test=pr_test,
            explanation=pr_explanation,
            code_diff=code_diff,
        )
        response = llm.invoke(code_diff_summary_input)
        track_llm_usage(db, usage_log_id, response, ModelNames.GPT_5)

        code_diff_summary = code_diff_summary_parser.invoke(response)
        assert isinstance(code_diff_summary, CodeDiffSummary), "code diff summary parsing failed"

        pr_text = f"Title: {pr.title}\n Tests: {pr_test}\n Explanation: {pr_explanation}\n Files changed: {files}\n Code diff summary: {code_diff_summary.pull_request_description}"
        pr_embedding = embedding_model.embed_query(pr_text)

        return PullRequest(
            id=pr.number,
            title=pr.title,
            test=pr_test,
            explanation=pr_explanation,
            files=files,
            embedding=pr_embedding,
            code_diff_summary=code_diff_summary.pull_request_description,
            linked_issue_ids=linked_issue_ids,
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


def _parse_linked_issue_ids(body: str, repo_name: str) -> list[int] | None:
    pattern = (
        rf"\$\s*#(\d+)"  # $ #1234
        rf"|\$\s*https://[^\s]*/{re.escape(repo_name)}/issues/(\d+)"  # $ https://.../issues/1234
        rf"|\$\s*\[#(\d+)\]\(https://[^\s]*/{re.escape(repo_name)}/issues/\d+\)"  # $ [#1234](https://.../issues/1234)
    )
    matches = re.findall(pattern, body)
    return [int(m[0] or m[1] or m[2]) for m in matches] if matches else None


def _parse_explanation(body: str) -> str:
    pattern = r"### Explanation of Change(.*?)### Fixed Issues"
    match = re.search(pattern, body, re.DOTALL | re.IGNORECASE)
    if not match:
        return ""

    raw_section = match.group(1).strip()
    without_comments = re.sub(r"<!--.*?-->", "", raw_section, flags=re.DOTALL)
    normalized_spacing = re.sub(r"\n{3,}", "\n\n", without_comments)

    return normalized_spacing.strip()


def add_pull_request_if_not_exist(
    pull_request_id: int, repo_id: int, repo_client: Repository, db: Database, usage_log_id: int | None = None
) -> PullRequest | None:
    existing_pr = db.get_pull_request_by_id_with_embedding(pull_request_id, repo_id)
    if existing_pr:
        return existing_pr

    pull_request = _get_pr_with_embeddings(pull_request_id, repo_client, db, usage_log_id)
    if not pull_request:
        logging.error(f"failed to fetch pull request {pull_request_id}")
        return None

    db.add_pull_request(pull_request, repo_id)
    return pull_request


def get_pull_request_diffs(
    pull_request_id: int,
    repo_client: Repository,
    gitignore_spec: pathspec.PathSpec,
    since_commit_sha: str | None = None,
) -> tuple[PullRequest, list[PRFileDiff]]:
    try:
        pr = repo_client.get_pull(pull_request_id)

        all_files = list(pr.get_files())

        if since_commit_sha:
            comparison = repo_client.compare(since_commit_sha, pr.head.sha)
            files_to_review = list(comparison.files)
        else:
            files_to_review = all_files

        pr_test = _parse_test_steps(pr.body or "")
        pr_explanation = _parse_explanation(pr.body or "")
        linked_issue_ids = _parse_linked_issue_ids(pr.body or "", repo_client.name)

        files_without_ignored = [f for f in files_to_review if not gitignore_spec.match_file(f.filename)]
        files = [f.filename for f in files_without_ignored]

        pull_request_model = PullRequest(
            id=pr.number,
            title=pr.title,
            test=pr_test,
            explanation=pr_explanation,
            files=files,
            linked_issue_ids=linked_issue_ids,
            commit_sha=pr.head.sha,
        )

        pr_diffs = []
        for file in files_without_ignored:
            pr_diff = PRFileDiff(
                filename=file.filename,
                status=file.status,
                additions=file.additions,
                deletions=file.deletions,
                patch=file.patch,
            )
            pr_diffs.append(pr_diff)

        return pull_request_model, pr_diffs

    except Exception as e:
        logging.error(f"failed to get PR diffs for {pull_request_id}: {e}")
        raise


def create_pull_request_review(
    pull_request_id: int,
    review_data: LineByLineCodeReview,
    commit_sha: str,
    repo_client: Repository,
    last_reviewed_sha: str | None = None,
) -> None:
    """Create a single GitHub review with body and multiple line comments for specific repo"""
    try:
        pr = repo_client.get_pull(pull_request_id)

        incremental_notice = (
            f"**This review covers only the changes made since the last review (commit {last_reviewed_sha[:7]}), not the entire PR.**\nUse `full review` to review entire PR\n"
            if last_reviewed_sha
            else ""
        )
        review_body = f"{incremental_notice}{review_data.code_overview}{SIGNATURE}"

        # Get PR files to validate paths and line numbers
        pr_files = list(pr.get_files())
        valid_paths = {f.filename for f in pr_files}

        review_comments = []
        for comment in review_data.comments:
            if is_allowed_comment_type(comment.label):
                if comment.file not in valid_paths:
                    continue

                comment_data = {
                    "path": comment.file,
                    "body": f"**{comment.label.value}**: {comment.content}{SIGNATURE}",
                    "line": comment.line,
                    "side": "RIGHT",
                }

                # Add start_line if it's a multi-line comment
                if comment.start_line and comment.start_line < comment.line:
                    comment_data["start_line"] = comment.start_line
                    comment_data["start_side"] = "RIGHT"

                review_comments.append(comment_data)

        if not is_production_environment():
            logger.info(f"skip for non prod environment. {len(review_comments)}, {review_body}\n {review_comments}")
            return

        commit = repo_client.get_commit(commit_sha)
        pr.create_review(body=review_body, event="COMMENT", comments=review_comments, commit=commit)  # type: ignore[arg-type]
        logger.info(f"created review for #{pull_request_id} with {len(review_comments)} comments")

    except Exception as e:
        logger.error(f"failed to create PR review for #{pull_request_id}: {e}")
        raise
