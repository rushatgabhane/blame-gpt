from typing import List
import re
from libs.github import gh, repo
from models.models import PullRequest
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
from libs.llm import embedding_model
from libs.sqlite.sqlite_client import Database

logger = logging.getLogger(__name__)


def get_pull_requests_between(base: str, head: str) -> List[int] | None:
    comparison = repo.compare(base=base, head=head)

    pr_numbers = set()
    for commit in comparison.commits:
        match = re.search(r"Merge pull request #(\d+)", commit.commit.message)
        if match:
            pr_numbers.add(int(match.group(1)))

    return sorted(list(pr_numbers)) if pr_numbers else None


def add_new_pull_requests_between(
    base: str, head: str, issue_id: int, db: Database
) -> List[PullRequest] | None:
    new_ids = get_pull_requests_between(base, head)
    if not new_ids:
        return

    for pr_id in new_ids:
        db.add_issue_pull_request(issue_id, pr_id)

    logging.info(f"found {len(new_ids)} new pull requests {new_ids}")
    existing_ids = db.get_existing_pr_ids()
    new_ids_to_process = [pr_id for pr_id in new_ids if pr_id not in existing_ids]
    if not new_ids_to_process:
        logging.info("no new pull requests to process")
        return

    result: List[PullRequest] = []

    logging.info(
        f"processing {len(new_ids_to_process)} new pull requests: {new_ids_to_process}"
    )

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {
            executor.submit(fetch_pr, pr_id): pr_id for pr_id in new_ids_to_process
        }
        for future in as_completed(futures):
            pull_request = future.result()
            if pull_request:
                db.add_pull_request(pull_request)
                result.append(pull_request)

    return result


def fetch_pr(pr_id: int) -> PullRequest | None:
    try:
        pr = repo.get_pull(pr_id)
        files = [f.filename for f in pr.get_files()]

        pr_test = parse_test_steps(pr.body or "")
        pr_explaination = parse_explaination(pr.body or "")

        pr_text = f"Title: {pr.title}\n Tests: {pr_test}\n Explaination: {pr_explaination}\n Files changed: {files}"
        pr_embedding = embedding_model.embed_query(pr_text)

        return PullRequest(
            id=pr.number,
            title=pr.title,
            test=pr_test,
            explaination=parse_explaination(pr.body or ""),
            files=files,
            embedding=pr_embedding,
        )
    except Exception as e:
        logging.error(f"failed to fetch PR {pr_id}: {e}")
        return None


def parse_test_steps(body: str) -> str:
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


def parse_explaination(body: str) -> str:
    pattern = r"### Explanation of Change(.*?)### Fixed Issues"
    match = re.search(pattern, body, re.DOTALL | re.IGNORECASE)
    if not match:
        return ""

    raw_section = match.group(1).strip()
    without_comments = re.sub(r"<!--.*?-->", "", raw_section, flags=re.DOTALL)
    normalized_spacing = re.sub(r"\n{3,}", "\n\n", without_comments)

    return normalized_spacing.strip()
