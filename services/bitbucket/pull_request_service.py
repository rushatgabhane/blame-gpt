import logging

import pathspec
import requests

from libs import bitbucket
from libs.constants import SIGNATURE
from libs.helpers import is_production_environment
from models.models import LineByLineCodeReview, PRFileDiff, PullRequest
from services.diff_service import split_raw_diff
from services.review_service import is_allowed_comment_type

logger = logging.getLogger(__name__)


def get_pull_request_diffs(
    workspace: str,
    repo: str,
    pull_request: dict,
    gitignore_spec: pathspec.PathSpec,
    incremental_diff: str | None = None,
) -> tuple[PullRequest, list[PRFileDiff]]:
    """Build file diffs from the API (full review) or from a locally computed
    incremental diff covering only the commits since the last review."""
    pull_request_id = pull_request["id"]

    if incremental_diff is not None:
        patches = split_raw_diff(incremental_diff)
        diffs = [
            _file_diff_from_patch(filename, patch)
            for filename, patch in patches.items()
            if not gitignore_spec.match_file(filename)
        ]
    else:
        raw = bitbucket.get_pull_request_diff(workspace, repo, pull_request_id)
        stats = bitbucket.get_pull_request_diffstat(workspace, repo, pull_request_id)
        patches = split_raw_diff(raw)
        diffs = []
        for stat in stats:
            new = stat.get("new") or {}
            old = stat.get("old") or {}
            filename = new.get("path") or old.get("path") or ""
            if not filename or gitignore_spec.match_file(filename):
                continue

            diff = PRFileDiff(
                filename=filename,
                status=stat.get("status", "modified"),
                additions=stat.get("lines_added", 0),
                deletions=stat.get("lines_removed", 0),
                patch=patches.get(filename),
            )
            diffs.append(diff)

    model = PullRequest(
        id=pull_request_id,
        title=pull_request.get("title", ""),
        test="",
        explanation=pull_request.get("description") or "",
        files=[diff.filename for diff in diffs],
        commit_sha=pull_request["source"]["commit"]["hash"],
    )
    return model, diffs


def _file_diff_from_patch(filename: str, patch: str) -> PRFileDiff:
    header = patch.split("\n@@", 1)[0]
    status = "modified"
    if "new file mode" in header:
        status = "added"
    if "deleted file mode" in header:
        status = "removed"

    lines = patch.splitlines()
    additions = sum(1 for line in lines if line.startswith("+") and not line.startswith("+++"))
    deletions = sum(1 for line in lines if line.startswith("-") and not line.startswith("---"))

    return PRFileDiff(filename=filename, status=status, additions=additions, deletions=deletions, patch=patch)


def create_pull_request_review(
    workspace: str,
    repo: str,
    pull_request_id: int,
    review_data: LineByLineCodeReview,
    last_reviewed_sha: str | None = None,
) -> None:
    """Post a review as one summary comment plus inline comments (Bitbucket has no review object)."""
    incremental_notice = (
        f"**This review covers only the changes made since the last review (commit {last_reviewed_sha[:7]}), not the entire PR.**\nUse `full review` to review entire PR\n"
        if last_reviewed_sha
        else ""
    )
    review_body = f"{incremental_notice}{review_data.code_overview}{SIGNATURE}"
    valid_paths = set(review_data.files_reviewed or [])

    comments = [
        comment
        for comment in review_data.comments
        if is_allowed_comment_type(comment.label) and comment.file in valid_paths
    ]

    if not is_production_environment():
        logger.info(f"skip for non prod environment. {len(comments)}, {review_body}\n {comments}")
        return

    bitbucket.add_pull_request_comment(workspace, repo, pull_request_id, review_body)

    posted = 0
    for comment in comments:
        markdown = f"**{comment.label.value}**: {comment.content}{SIGNATURE}"
        try:
            bitbucket.add_pull_request_comment(
                workspace, repo, pull_request_id, markdown, path=comment.file, line=comment.line
            )
            posted += 1
        except requests.HTTPError as e:
            # a comment on a line outside the diff is rejected; don't fail the whole review
            logger.error(f"failed to add inline comment on {comment.file}:{comment.line}: {e}")

    logger.info(f"created review for #{pull_request_id} with {posted} comments")
