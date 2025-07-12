import asyncio
import logging
import os
from datetime import UTC, datetime

import httpx
from fastapi import FastAPI
from github.Notification import Notification

from libs import constants
from libs.github import gh_user
from libs.helpers import now_8601, now_rfc1123
from libs.llm import llmNano
from libs.prompt_templates.command_classification import command_classification_parser, command_classifier_prompt
from libs.sqlite.core.core_sqlite_client import Database as CoreDatabase
from libs.sqlite.docs.docs_sqlite_client import Database as DocsDatabase
from models.enums import CommandName
from models.models import CommandClassification
from services import blame_pipeline, user_service
from services.github.comment_service import get_comment, react_comment

logger = logging.getLogger(__name__)
logging.getLogger("httpx").setLevel(logging.WARNING)


async def listen_notifications(core_db: CoreDatabase, docs_db: DocsDatabase, app: FastAPI):
    previous_since = now_8601(nowUTC=app.state.last_checked)
    previous_last_checked = now_rfc1123(nowUTC=app.state.last_checked)

    headers = {
        "If-Modified-Since": previous_last_checked,
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"Bearer {os.getenv('GITHUB_TOKEN')}",
    }
    params = {
        "since": previous_since,
        "participating": "true",
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url="https://api.github.com/notifications", headers=headers, params=params)

        if response.status_code == 304:
            return

        if response.status_code != 200:
            logger.error(f"failed to fetch notifications, status code: {response.status_code}")
            return

        app.state.last_checked = datetime.now(UTC)

        notifications = response.json()

        if not notifications:
            logger.info(f"no new notifications found since {app.state.last_modified_notification}")
            return

        for data in notifications:
            n = _create_notification(data)
            if not _is_valid_notification(n):
                await _unsubscribe_notification(n)
                continue

            asyncio.create_task(_process_notification(n, core_db, docs_db))

    except httpx.RemoteProtocolError as e:
        logger.error(f"expected sometimes: remote protocol error while fetching notifications: {e}")
        return

    except Exception as e:
        logger.exception(f"error fetching notifications: {e}")


def _create_notification(n_dict: dict) -> Notification:
    n = Notification(gh_user._requester, {}, completed=False)
    n._useAttributes(n_dict)
    return n


def _get_issue_or_pr_id(n: Notification) -> int:
    return int(n.subject.url.split("/")[-1])


async def _process_notification(n: Notification, core_db: CoreDatabase, docs_db: DocsDatabase):
    issue_or_pull_request_id = _get_issue_or_pr_id(n)
    logger.info(f"processing notification {n.id} for #{issue_or_pull_request_id}")
    try:
        latest_comment_url = n.subject.latest_comment_url
        comment = get_comment(latest_comment_url)
        if not comment or constants.USER_TAG.lower() not in comment.body.lower():
            return

        asyncio.create_task(react_comment(latest_comment_url, "eyes"))

        command_name = _classify_command(comment.body)
        await _run_command(command_name, n, core_db, docs_db)

        asyncio.create_task(_unsubscribe_notification(n))

        userID = user_service.add_user_if_not_exists(
            username=comment.user.login,
            email=comment.user.email or "",
            name=comment.user.name or comment.user.login,
            avatar_url=comment.user.avatar_url,
            core_db=core_db,
        )

        user_service.add_user_usage_log(
            userID=userID,
            command_name=command_name,
            comment_url=latest_comment_url,
            output="default output",  # Placeholder, replace later.
            issue_or_pull_request_url=n.subject.url,
            core_db=core_db,
            comment_text=comment.body,
        )
    except Exception as e:
        logger.error(f"#{issue_or_pull_request_id} {n.id}: error processing notification : {n} : {e}")


async def _unsubscribe_notification(n: Notification):
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"Bearer {os.getenv('GITHUB_TOKEN')}",
    }
    async with httpx.AsyncClient() as client:
        res = await client.delete(url=n.subscription_url, headers=headers)

    if res.status_code == 204:
        logger.info(f"{_get_issue_or_pr_id(n)}: {n.id}: unsubscribed from notification")
    else:
        logger.error(
            f"{_get_issue_or_pr_id(n)}: {n.id}: failed to unsubscribe from notification, status code: {res.status_code}"
        )


def _is_valid_notification(notification: Notification) -> bool:
    if notification.reason != "mention":
        return False

    if notification.subject.type != "Issue" and notification.subject.type != "PullRequest":
        return False

    if not notification.subject.latest_comment_url:
        logger.warning(f"{notification.id}: notification has no latest comment URL, skipping")
        return False

    if (
        notification.repository.name != constants.REPO_NAME
        and notification.repository.owner.login != constants.REPO_OWNER
    ):
        logger.warning(f"{notification.id}: notification is from {notification.repository}, skipping")
        return False

    return True


def _classify_command(comment_body: str) -> CommandName:
    # Trim to prevent abuse
    comment_trimmed = " ".join(comment_body.split()[:100])
    try:
        input = command_classifier_prompt.format(
            comment=comment_trimmed,
        )
        response = llmNano.invoke(input)
        classification: CommandClassification = command_classification_parser.invoke(response)
        return CommandName(classification.command_name)
    except Exception as e:
        logger.error(f"failed to classify command for comment {comment_trimmed}: {e}")
        return CommandName.UNKNOWN


async def _run_command(command_name: CommandName, n: Notification, core_db: CoreDatabase, docs_db: DocsDatabase):
    issue_or_pull_request_id = _get_issue_or_pr_id(n)
    if command_name == CommandName.BLAME and n.subject.type == "Issue":
        async for step in blame_pipeline.run(issue_id=issue_or_pull_request_id, db=core_db):
            logger.info(f"{n.id}: #{issue_or_pull_request_id} {step}")
        return

    if command_name == CommandName.OHMYDOCS:
        logger.info(f"{n.id}: ohmydocs command received for notification {n.id}, but not implemented yet.")
        # Disable until it works well.
        # await run_graph.docs(pull_request_id=issue_or_pull_request_id, db=core_db, docs_db=docs_db)
        return

    if command_name == CommandName.TEST_STEPS:
        logger.info(f"{n.id}: test steps command received for notification {n.id}, but not implemented yet.")
        # Disable until it works well.
        # async for step in test_steps_pipeline.run(pull_request_id=issue_or_pull_request_id, db=core_db):
        #     logger.info(f"{notification.id}: #{issue_or_pull_request_id} {step}")
        return

    await react_comment(n.subject.latest_comment_url, "-1")
    logger.info(f"{n.id}: unknown command for notification {n.id}, skipping")
