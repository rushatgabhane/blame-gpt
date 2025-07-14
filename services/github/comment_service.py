import logging
import random

import httpx
from github.IssueComment import IssueComment

from libs.github import gh_user, github_token, repo
from libs.helpers import is_production_environment
from models.models import CulpritPullRequest

logger = logging.getLogger(__name__)
logging.getLogger("httpx").setLevel(logging.WARNING)


async def add_comment(issue_number: int, culprit_pull_requests: list[CulpritPullRequest]) -> str:
    try:
        comment = _format_comment(culprit_pull_requests)
        if not is_production_environment():
            logger.info(f"skipping comment creation in non production environment {comment}")
            return comment

        repo.get_issue(number=issue_number).create_comment(comment)
        return comment
    except Exception as e:
        logger.error(f"error adding comment to issue #{issue_number}: {e}")
        raise


_sassy_culprit_titles = [
    "Possible culprit PRs for this issue",
    "Sus PRs on the scene",
    "Who let the bugs out? 🐛",
    "Lowkey sus PRs fr fr",
    "Vibe check failed for these PRs 💅",
    "Suspects on the loose 🕵",
    "Needs a vibe check ASAP",
    "No cap, these PRs acting up",
]


def _format_comment(culprit_pull_requests: list[CulpritPullRequest]) -> str:
    if not culprit_pull_requests:
        return ""

    random.seed()
    comment = f"### {random.choice(_sassy_culprit_titles)}\n"
    for i, pr in enumerate(culprit_pull_requests):
        if i == 2:
            comment += "\n#### If not above, check these\n"
        comment += f"- #{pr.pull_request_id}: {pr.reason}\n"
    return comment


def add_comment_to_pull_request(pull_request_id: int, comment: str) -> str:
    try:
        if is_production_environment():
            repo.get_pull(pull_request_id).create_issue_comment(comment)
            return comment

        logger.info("skipping comment creation to PR in non production environment")
        return comment

    except Exception as e:
        logger.error(f"error adding comment to pull request #{pull_request_id}: {e}")
        raise


async def react_comment(comment_url: str, emoji: str):
    if not is_production_environment():
        logger.info(f"skipping reaction to comment {comment_url} in non production environment")
        return

    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"Bearer {github_token.get_secret_value()}",
    }
    async with httpx.AsyncClient() as client:
        res = await client.post(
            url=f"{comment_url}/reactions",
            headers=headers,
            json={"content": emoji},
        )

    if res.status_code != 201:
        logger.info(f"failed to react with {emoji} on comment {comment_url}/reactions, status code: {res.status_code}")


def get_comment(comment_url: str) -> IssueComment | None:
    try:
        _headers, data = gh_user._requester.requestJsonAndCheck(
            verb="GET",
            url=comment_url,
        )
        return IssueComment(requester=gh_user._requester, headers=_headers, attributes=data, completed=True)
    except Exception as e:
        logger.error(f"failed to get comment {comment_url}: {e}")
        return None
