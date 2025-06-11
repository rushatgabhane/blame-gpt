from libs.github import repo
import logging
from models.models import CulpritPullRequests

logger = logging.getLogger(__name__)


async def add_comment(issue_number: int, culprit_pull_requests: CulpritPullRequests) -> str:
    try:
        comment = format_comment(culprit_pull_requests)
        repo.get_issue(number=issue_number).create_comment(comment)
        return comment
    except Exception as e:
        logger.error(f"error adding comment to issue #{issue_number}: {e}")
        raise


def format_comment(culprit_pull_requests: CulpritPullRequests) -> str:
    if not culprit_pull_requests.pull_requests:
        return ""

    comment = "### Possible culprit PRs for this issue\n"
    for i, pr in enumerate(culprit_pull_requests.pull_requests):
        if i == 2:
            comment += f"\n#### Exploratory PRs\n"
        comment += f"- #{pr.pull_request_id}: {pr.reason}\n"
    return comment


def add_comment_to_pull_request(pull_request_id: int, comment: str) -> None:
    try:
        pull_request = repo.get_pull(pull_request_id)
        pull_request.create_issue_comment(comment)
    except Exception as e:
        logger.error(f"error adding comment to pull request #{pull_request_id}: {e}")
        raise
