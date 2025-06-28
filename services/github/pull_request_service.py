from typing import List, Optional
import re
from libs.github import repo
from models.models import PullRequest, FilePatch
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
from libs.llm import embedding_model
from libs.sqlite.core.core_sqlite_client import Database
import sqlite3

logger = logging.getLogger(__name__)


def _get_pull_requests_between(base: str, head: str) -> List[int] | None:
    comparison = repo.compare(base=base, head=head)

    pr_numbers = set()
    for commit in comparison.commits:
        match = re.search(r"Merge pull request #(\d+)", commit.commit.message)
        if match:
            pr_numbers.add(int(match.group(1)))

    return sorted(list(pr_numbers)) if pr_numbers else None


def add_new_pull_requests_between(base: str, head: str, issue_id: int, db: Database) -> List[PullRequest] | None:
    new_ids = _get_pull_requests_between(base, head)
    if not new_ids:
        return

    logging.info(f"{issue_id}: found {len(new_ids)} new pull requests {new_ids}")
    existing_ids = db.get_existing_pr_ids()
    new_ids_to_process = [pr_id for pr_id in new_ids if pr_id not in existing_ids]

    result: List[PullRequest] = []

    if not new_ids_to_process:
        logging.info("{issue_id} no new pull requests to process")
    else:
        logging.info(f"{issue_id}: processing {len(new_ids_to_process)} new pull requests")

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(_get_pr_with_embeddings, pr_id): pr_id for pr_id in new_ids_to_process}
        for future in as_completed(futures):
            pull_request = future.result()
            if pull_request:
                db.add_pull_request(pull_request)
                result.append(pull_request)

    for pr_id in new_ids:
        try:
            db.add_issue_pull_request(issue_id, pr_id)
        except sqlite3.IntegrityError as e:
            logging.error(f"failed to add issue pull request {issue_id} - {pr_id}: {e}")

    return result


def _get_pr_with_embeddings(pull_request_id: int) -> PullRequest | None:
    try:
        pr = repo.get_pull(pull_request_id)
        files = [f.filename for f in pr.get_files()]

        pr_test = _parse_test_steps(pr.body or "")
        pr_explaination = _parse_explaination(pr.body or "")

        pr_text = f"Title: {pr.title}\n Tests: {pr_test}\n Explaination: {pr_explaination}\n Files changed: {files}"
        pr_embedding = embedding_model.embed_query(pr_text)

        return PullRequest(
            id=pr.number,
            title=pr.title,
            test=pr_test,
            explaination=_parse_explaination(pr.body or ""),
            files=files,
            embedding=pr_embedding,
        )
    except Exception as e:
        logging.error(f"failed to fetch PR {pull_request_id}: {e}")
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


def get_pull_request_patch(pull_request_id: int) -> List[FilePatch]:
    patches: List[FilePatch] = []

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


def add_pull_request(pull_request_id: int, db: Database) -> Optional[PullRequest]:
    existing_pr = db.get_pull_request_by_id_with_embedding(pull_request_id)
    if existing_pr:
        return existing_pr

    pull_request = _get_pr_with_embeddings(pull_request_id)
    if not pull_request:
        logging.error(f"failed to fetch pull request {pull_request_id}")
        return None

    db.add_pull_request(pull_request)
    return pull_request
