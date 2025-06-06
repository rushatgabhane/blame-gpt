from libs.github import repo_secondary
import logging
from models.models import CulpritPullRequests

logger = logging.getLogger(__name__)


async def add_comment(issue_number: int, culprit_pull_requests: CulpritPullRequests) -> str:
    try:
        comment = format_comment(culprit_pull_requests)
        repo_secondary.get_issue(number=issue_number).create_comment(comment)
        return comment
    except Exception as e:
        logger.error(f"error adding comment to issue #{issue_number}: {e}")
        raise


def format_comment(culprit_pull_requests: CulpritPullRequests) -> str:
    if not culprit_pull_requests.pull_requests:
        return ""

    comment = "### Possible culprit PRs for this issue\n"
    for pr in culprit_pull_requests.pull_requests:
        comment += f"- #{pr.pull_request_id}: {pr.reason}\n"
    return comment
