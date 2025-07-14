import logging
import re
import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

from libs import constants
from libs.github import repo
from libs.llm import ModelNames, embedding_model, llmReasoningCheap
from libs.prompt_templates.code_diff_summary import code_diff_summary_parser, code_diff_summary_prompt
from libs.sqlite.core.core_sqlite_client import Database
from models.models import CodeDiffSummary, FilePatch, PullRequest
from services.user_service import track_llm_usage

logger = logging.getLogger(__name__)
_add_new_prs_lock = threading.Lock()


def _get_pull_requests_between(base: str, head: str) -> list[int] | None:
    """
    Retrieve the list of pull request numbers merged between two Git references.
    
    Parameters:
    	base (str): The base Git reference (e.g., branch or commit SHA).
    	head (str): The head Git reference (e.g., branch or commit SHA).
    
    Returns:
    	list[int] | None: Sorted list of unique pull request numbers merged between base and head, or None if none are found.
    """
    comparison = repo.compare(base=base, head=head)

    pr_numbers = set()
    for commit in comparison.commits:
        match = re.search(r"Merge pull request #(\d+)", commit.commit.message)
        if match:
            pr_numbers.add(int(match.group(1)))

    return sorted(list(pr_numbers)) if pr_numbers else None


def add_new_pull_requests_between(base: str, head: str, issue_id: int, db: Database, usage_log_id: int | None = None) -> None:
    """
    Adds all pull requests merged between two Git references to the database and links them to a specified issue.
    
    This function identifies PRs merged between the given `base` and `head` references, processes any new PRs by fetching their data and embeddings, stores them in the database, and associates all found PRs with the provided issue ID. Processing is performed concurrently for efficiency. Existing PRs are not duplicated, and database integrity errors during linking are logged as warnings.
    
    Parameters:
        base (str): The base Git reference.
        head (str): The head Git reference.
        issue_id (int): The ID of the issue to link PRs to.
        usage_log_id (int, optional): An identifier for tracking LLM usage, if provided.
    """
    with _add_new_prs_lock:
        new_ids = _get_pull_requests_between(base, head)
        if not new_ids:
            return

        logging.info(f"{issue_id}: found {len(new_ids)} new pull requests {new_ids}")
        existing_ids = db.get_existing_pr_ids()
        new_ids_to_process = [pr_id for pr_id in new_ids if pr_id not in existing_ids]
        logging.info(f"{issue_id}: processing {len(new_ids_to_process)} new pull requests")

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(_get_pr_with_embeddings, pr_id, db, usage_log_id): pr_id for pr_id in new_ids_to_process}
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
    """
    Fetches and filters the raw diff text from a GitHub diff URL, returning only changes to files under `src/` excluding those in `src/languages`.
    
    Parameters:
        diff_url (str): The URL to the GitHub diff resource.
    
    Returns:
        str: The filtered diff text, or an empty string if fetching fails or no relevant changes are found.
    """
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


def _get_pr_with_embeddings(pull_request_id: int, db: Database, usage_log_id: int | None = None) -> PullRequest | None:
    """
    Fetches a GitHub pull request by ID, summarizes its code diff using an LLM, generates an embedding, and returns a populated PullRequest object.
    
    Parameters:
        pull_request_id (int): The numeric ID of the pull request to fetch and process.
    
    Returns:
        PullRequest | None: A PullRequest object containing extracted metadata, code diff summary, and embedding, or None if processing fails.
    """
    try:
        pr = repo.get_pull(pull_request_id)
        all_files = pr.get_files()

        files = [f.filename for f in all_files]

        pr_test = _parse_test_steps(pr.body or "")
        linked_issue_ids = _parse_linked_issue_ids(pr.body or "")
        pr_explaination = _parse_explaination(pr.body or "")

        code_diff = _get_code_diff(pr.diff_url)
        code_diff_summary_input = code_diff_summary_prompt.format(
            title=pr.title,
            test=pr_test,
            explanation=pr_explaination,
            code_diff=code_diff,
        )
        response = llmReasoningCheap.invoke(code_diff_summary_input)
        track_llm_usage(db, usage_log_id, response, ModelNames.O3_MINI)
        
        code_diff_summary = code_diff_summary_parser.invoke(response)
        assert isinstance(code_diff_summary, CodeDiffSummary), "code diff summary parsing failed"

        pr_text = f"Title: {pr.title}\n Tests: {pr_test}\n Explaination: {pr_explaination}\n Files changed: {files}\n Code diff summary: {code_diff_summary.pull_request_description}"
        pr_embedding = embedding_model.embed_query(pr_text)

        return PullRequest(
            id=pr.number,
            title=pr.title,
            test=pr_test,
            explaination=pr_explaination,
            files=files,
            embedding=pr_embedding,
            code_diff_summary=code_diff_summary.pull_request_description,
            code_diff=code_diff,
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


def _parse_linked_issue_ids(body: str) -> list[int] | None:
    pattern = (
        rf"\$\s*#(\d+)"  # $ #1234
        rf"|\$\s*https://[^\s]*/{constants.REPO_NAME}/issues/(\d+)"  # $ https://.../issues/1234
        rf"|\$\s*\[#(\d+)\]\(https://[^\s]*/{constants.REPO_NAME}/issues/\d+\)"  # $ [#1234](https://.../issues/1234)
    )
    matches = re.findall(pattern, body)
    return [int(m[0] or m[1] or m[2]) for m in matches] if matches else None


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
    """
    Retrieve the list of file patches for a given pull request.
    
    Returns:
        A list of FilePatch objects, each containing the filename and patch text for files changed in the pull request that have non-empty patch data.
    """
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


def add_pull_request_if_not_exist(pull_request_id: int, db: Database, usage_log_id: int | None = None) -> PullRequest | None:
    """
    Fetches and stores a pull request with embeddings if it does not already exist in the database.
    
    If the pull request is already present with embeddings, returns it immediately. Otherwise, retrieves the pull request, processes it to generate embeddings, stores it in the database, and returns the stored object.
    
    Parameters:
        pull_request_id (int): The ID of the pull request to fetch and store.
        usage_log_id (int | None): Optional ID for tracking LLM usage.
    
    Returns:
        PullRequest | None: The pull request object with embeddings, or None if fetching fails.
    """
    existing_pr = db.get_pull_request_by_id_with_embedding(pull_request_id)
    if existing_pr:
        return existing_pr

    pull_request = _get_pr_with_embeddings(pull_request_id, db, usage_log_id)
    if not pull_request:
        logging.error(f"failed to fetch pull request {pull_request_id}")
        return None

    db.add_pull_request(pull_request)
    return pull_request
