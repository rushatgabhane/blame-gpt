import logging
import re
import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

import pathspec
import requests
from github.Repository import Repository

from libs import constants
from libs.github import repo
from libs.helpers import is_production_environment
from libs.llm import ModelNames, embedding_model, llm
from libs.prompt_templates.code_diff_summary import code_diff_summary_parser, code_diff_summary_prompt
from libs.sqlite.core.core_sqlite_client import Database
from models.enums import CodeReviewCommentType
from models.models import CodeDiffSummary, FilePatch, LineByLineCodeReview, PRDiff, PullRequest
from services.user_service import track_llm_usage

logger = logging.getLogger(__name__)
_add_new_prs_lock = threading.Lock()


def _get_pull_requests_between(base: str, head: str) -> list[int] | None:
    comparison = repo.compare(base=base, head=head)

    pr_numbers = set()
    for commit in comparison.commits:
        # Ignores reverted PRs by design
        match = re.search(r"^Merge pull request #(\d+)", commit.commit.message)
        if match:
            pr_numbers.add(int(match.group(1)))

    return sorted(list(pr_numbers)) if pr_numbers else None


def add_new_pull_requests_between(
    base: str, head: str, issue_id: int, db: Database, usage_log_id: int | None = None
) -> None:
    with _add_new_prs_lock:
        new_ids = _get_pull_requests_between(base, head)
        if not new_ids:
            return

        logging.info(f"{issue_id}: found {len(new_ids)} new pull requests {new_ids}")
        existing_ids = db.get_existing_pr_ids()
        new_ids_to_process = [pr_id for pr_id in new_ids if pr_id not in existing_ids]
        logging.info(f"{issue_id}: processing {len(new_ids_to_process)} new pull requests")

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {
                executor.submit(_get_pr_with_embeddings, pr_id, db, usage_log_id): pr_id for pr_id in new_ids_to_process
            }
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


def _get_pr_with_embeddings(pull_request_id: int, db: Database, usage_log_id: int | None = None) -> PullRequest | None:
    try:
        pr = repo.get_pull(pull_request_id)
        all_files = pr.get_files()

        files = [f.filename for f in all_files]

        pr_test = _parse_test_steps(pr.body or "")
        linked_issue_ids = _parse_linked_issue_ids(pr.body or "")
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


def _parse_explanation(body: str) -> str:
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


def add_pull_request_if_not_exist(
    pull_request_id: int, db: Database, usage_log_id: int | None = None
) -> PullRequest | None:
    existing_pr = db.get_pull_request_by_id_with_embedding(pull_request_id)
    if existing_pr:
        return existing_pr

    pull_request = _get_pr_with_embeddings(pull_request_id, db, usage_log_id)
    if not pull_request:
        logging.error(f"failed to fetch pull request {pull_request_id}")
        return None

    db.add_pull_request(pull_request)
    return pull_request


def _get_gitignore_spec(repo_ref: Repository) -> pathspec.PathSpec:
    """
    Get gitignore patterns from root .gitignore only
    TODO: Ignore gitignores from nested dirs too.
    """
    try:
        gitignore_files = repo_ref.get_contents(".gitignore")
        if not isinstance(gitignore_files, list):
            gitignore_files = [gitignore_files]

        all_patterns = []
        for file in gitignore_files:
            content = file.decoded_content.decode("utf-8")
            all_patterns.extend(content.splitlines())
        return pathspec.PathSpec.from_lines("gitwildmatch", all_patterns)
    except Exception:
        return pathspec.PathSpec.from_lines("gitwildmatch", [])


def get_pull_request_diffs(pull_request_id: int, repo_ref: Repository) -> tuple[PullRequest, list[PRDiff]]:
    try:
        pr = repo_ref.get_pull(pull_request_id)
        all_files = list(pr.get_files())

        gitignore_spec = _get_gitignore_spec(repo_ref)

        pr_test = _parse_test_steps(pr.body or "")
        pr_explanation = _parse_explanation(pr.body or "")
        linked_issue_ids = _parse_linked_issue_ids(pr.body or "")

        files_without_ignored = [f for f in all_files if not gitignore_spec.match_file(f.filename)]
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
            pr_diff = PRDiff(
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


def format_pr_diffs_for_review(pr_diffs: list[PRDiff]) -> str:
    """Format PR diffs with embedded line numbers"""
    formatted_diffs = []

    for diff in pr_diffs:
        if not diff.patch:
            continue

        formatted_diff = f"## File: {diff.filename}\n"
        formatted_diff += f"Status: {diff.status}\n"
        formatted_diff += f"Changes: +{diff.additions} -{diff.deletions}\n\n"

        numbered_patch = _add_line_numbers_to_patch(diff.patch)
        formatted_diff += numbered_patch

        formatted_diffs.append(formatted_diff)

    return "\n\n".join(formatted_diffs)


def _add_line_numbers_to_patch(patch: str) -> str:
    lines = patch.split("\n")
    numbered_lines = []
    current_new_line = None

    for line in lines:
        # Parse hunk headers to get starting line numbers
        if line.startswith("@@"):
            # Extract new file line number from hunk header like "@@ -10,7 +10,8 @@"
            match = re.search(r"@@\s*-\d+,?\d*\s*\+(\d+),?\d*\s*@@", line)
            if match:
                current_new_line = int(match.group(1))
            numbered_lines.append(line)  # Keep hunk headers as is
            continue

        # Skip file headers
        if line.startswith("+++") or line.startswith("---"):
            numbered_lines.append(line)
            continue

        # Only process if we have a valid starting line number
        if current_new_line is None:
            numbered_lines.append(line)
            continue

        # Add line numbers: "109 +    some_code_here"
        if line.startswith("+"):
            numbered_lines.append(f"{current_new_line} {line}")
            current_new_line += 1
        elif line.startswith("-"):
            numbered_lines.append(line)  # Don't number removed lines
            # Don't increment for deleted lines
        else:
            # Context line (unchanged) - add line number and increment
            numbered_lines.append(f"{current_new_line} {line}")
            current_new_line += 1

    return "\n".join(numbered_lines)


def create_pull_request_review(
    pull_request_id: int, review_data: LineByLineCodeReview, commit_sha: str, repo_ref: Repository
) -> None:
    """Create a single GitHub review with body and multiple line comments for specific repo"""
    try:
        pr = repo_ref.get_pull(pull_request_id)

        review_body = f"{review_data.code_overview}"

        review_comments = []
        for comment in review_data.comments:
            if comment.label == CodeReviewCommentType.ISSUE or comment.label == CodeReviewCommentType.SUGGESTION:
                review_comments.append(
                    {
                        "path": comment.file,
                        "body": f"**{comment.label.value}**: {comment.content}",
                        "line": comment.line,
                        "side": "RIGHT",
                    }
                )

        if not is_production_environment():
            logger.info(f"skip for non prod environment. {len(review_comments)}, {review_body}\n {review_comments}")
            return

        commit = repo_ref.get_commit(commit_sha)
        pr.create_review(body=review_body, event="COMMENT", comments=review_comments, commit=commit)  # type: ignore[arg-type]
        logger.info(f"created PR review for #{pull_request_id} with {len(review_comments)} comments")

    except Exception as e:
        logger.error(f"failed to create PR review for #{pull_request_id}: {e}")
        raise
