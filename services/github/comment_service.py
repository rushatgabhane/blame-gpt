import logging
import os
import random

import httpx
from github.IssueComment import IssueComment

from libs.github import gh_user, repo
from models.models import CulpritPullRequest

logger = logging.getLogger(__name__)
logging.getLogger("httpx").setLevel(logging.WARNING)

sassy_culprit_titles = [
    "Possible culprit PRs for this issue",
    "Sus PRs on the scene",
    "Who let the bugs out? 🐛",
    "Lowkey sus PRs fr fr",
    "Vibe check failed for these PRs 💅",
    "Suspects on the loose 🕵",
    "Needs a vibe check ASAP",
    "No cap, these PRs acting up",
]


async def add_comment(issue_number: int, culprit_pull_requests: list[CulpritPullRequest]) -> str:
    try:
        comment = format_comment(culprit_pull_requests)
        if os.getenv("ENVIRONMENT") != "production":
            logger.info("skipping comment creation in non production environment {comment}")
            return comment

        repo.get_issue(number=issue_number).create_comment(comment)
        return comment
    except Exception as e:
        logger.error(f"error adding comment to issue #{issue_number}: {e}")
        raise


def format_comment(culprit_pull_requests: list[CulpritPullRequest]) -> str:
    if not culprit_pull_requests:
        return ""

    random.seed()
    comment = f"### {random.choice(sassy_culprit_titles)}\n"
    for i, pr in enumerate(culprit_pull_requests):
        if i == 2:
            comment += "\n#### If not above, check these\n"
        comment += f"- #{pr.pull_request_id}: {pr.reason}\n"
    return comment


def add_comment_to_pull_request(pull_request_id: int, comment: str) -> str:
    try:
        if os.getenv("ENVIRONMENT") == "production":
            pull_request = repo.get_pull(pull_request_id)
            pull_request.create_issue_comment(comment)
            return comment

        logger.info("skipping comment creation to PR in non-production environment")
        return comment

    except Exception as e:
        logger.error(f"error adding comment to pull request #{pull_request_id}: {e}")
        raise


async def react_comment(comment_url: str, emoji: str):
    if os.getenv("ENVIRONMENT") != "production":
        logger.info(f"skipping reaction to comment {comment_url} in non production environment")
        return

    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"Bearer {os.getenv('GITHUB_TOKEN')}",
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
