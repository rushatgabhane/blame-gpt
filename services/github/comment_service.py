import logging
import os

from libs.github import repo
from models.models import CulpritPullRequest

logger = logging.getLogger(__name__)


async def add_comment(issue_number: int, culprit_pull_requests: list[CulpritPullRequest]) -> str:
    try:
        comment = format_comment(culprit_pull_requests)
        if os.getenv("ENVIRONMENT") == "production":
            repo.get_issue(number=issue_number).create_comment(comment)
            return comment

        logger.info("skipping comment creation in non-production environment")
        return comment

    except Exception as e:
        logger.error(f"error adding comment to issue #{issue_number}: {e}")
        raise


def format_comment(culprit_pull_requests: list[CulpritPullRequest]) -> str:
    if not culprit_pull_requests:
        return ""

    comment = "### Possible culprit PRs for this issue\n"
    for i, pr in enumerate(culprit_pull_requests):
        if i == 2:
            comment += "\n#### If not above, check these\n"
        comment += f"- #{pr.pull_request_id}: {pr.reason}\n"
    return comment


def add_comment_to_pull_request(pull_request_id: int, comment: str) -> None:
    try:
        pull_request = repo.get_pull(pull_request_id)
        pull_request.create_issue_comment(comment)
    except Exception as e:
        logger.error(f"error adding comment to pull request #{pull_request_id}: {e}")
        raise
