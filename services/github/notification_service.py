import asyncio
import logging
from datetime import UTC, datetime

import httpx
from fastapi import FastAPI
from github.IssueComment import IssueComment
from github.Notification import Notification

from libs import constants
from libs.github import gh_user, github_token
from libs.helpers import now_8601, now_rfc1123, thinking_verb
from libs.llm import llmNano
from libs.prompt_templates.command_classification import command_classification_parser, command_classifier_prompt
from libs.sqlite.core.core_sqlite_client import Database as CoreDatabase
from libs.sqlite.docs.docs_sqlite_client import Database as DocsDatabase
from models.enums import CommandName
from models.models import CommandClassification
from services import blame_pipeline, user_service
from services.github.comment_service import (
    create_thinking_comment,
    create_thinking_comment_for_pr,
    get_comment,
    react_comment,
)
from services.test_step import test_step_pipeline

logger = logging.getLogger(__name__)
logging.getLogger("httpx").setLevel(logging.WARNING)


async def listen_notifications(core_db: CoreDatabase, docs_db: DocsDatabase, app: FastAPI):
    previous_since = now_8601(nowUTC=app.state.last_checked)
    previous_last_checked = now_rfc1123(nowUTC=app.state.last_checked)

    headers = {
        "If-Modified-Since": previous_last_checked,
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"Bearer {github_token.get_secret_value()}",
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

        tasks = []
        for data in notifications:
            n = _create_notification(data)
            if not _is_valid_notification(n):
                await _unsubscribe_notification(n)
                continue

            tasks.append(asyncio.create_task(_process_notification(n, core_db, docs_db)))
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

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

        react_task = asyncio.create_task(react_comment(latest_comment_url, "eyes"))

        command_name = _classify_command(comment.body, n.subject.type)

        userID = user_service.add_user_if_not_exists(
            username=comment.user.login,
            email=comment.user.email or "",
            name=comment.user.name or comment.user.login,
            avatar_url=comment.user.avatar_url,
            core_db=core_db,
        )

        usage_log_id = user_service.add_user_usage_log(
            userID=userID,
            command_name=command_name,
            comment_url=latest_comment_url,
            output="default output",  # Placeholder, replace later.
            issue_or_pull_request_url=n.subject.url,
            core_db=core_db,
            comment_text=comment.body,
        )

        should_process_again = _has_again(comment)

        await _run_command(
            command_name=command_name,
            n=n,
            core_db=core_db,
            docs_db=docs_db,
            usage_log_id=usage_log_id,
            should_process_again=should_process_again,
        )

        unsubscribe_task = asyncio.create_task(_unsubscribe_notification(n))

        # Wait for async tasks to complete
        await unsubscribe_task
        await react_task
    except Exception as e:
        logger.error(f"#{issue_or_pull_request_id} {n.id}: error processing notification : {n} : {e}")


async def _unsubscribe_notification(n: Notification):
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"Bearer {github_token.get_secret_value()}",
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


def _classify_command(comment_body: str, subject_type: str) -> CommandName:
    words = comment_body.split()
    user_tag_pos = next((i for i, word in enumerate(words) if constants.USER_TAG.lower() in word.lower()), None)

    if user_tag_pos:
        start = max(0, user_tag_pos - 10)
        end = min(len(words), user_tag_pos + 20)
        relevant_words = words[start:end]
    else:
        relevant_words = words[:50]

    comment_trimmed = " ".join(relevant_words)

    try:
        input = command_classifier_prompt.format(
            comment=comment_trimmed,
            type=subject_type,
            user_tag=constants.USER_TAG,
        )
        response = llmNano.invoke(input)
        classification: CommandClassification = command_classification_parser.invoke(response)
        return CommandName(classification.command_name)
    except Exception as e:
        logger.error(f"failed to classify command for comment {comment_trimmed}: {e}")
        return CommandName.UNKNOWN


async def _run_command(
    command_name: CommandName,
    n: Notification,
    core_db: CoreDatabase,
    docs_db: DocsDatabase,
    usage_log_id: int | None,
    should_process_again: bool = False,
):
    issue_or_pull_request_id = _get_issue_or_pr_id(n)
    if command_name == CommandName.BLAME and n.subject.type == "Issue":
        thinking_comment = create_thinking_comment(
            issue_number=issue_or_pull_request_id, thinking_text=f"{thinking_verb()}..."
        )
        async for step in blame_pipeline.run(
            issue_id=issue_or_pull_request_id, db=core_db, usage_log_id=usage_log_id, thinking_comment=thinking_comment
        ):
            # we don't wanna print the yield logs
            logger.debug(f"{n.id}: #{issue_or_pull_request_id} {step}")
        return

    if command_name == CommandName.OHMYDOCS:
        logger.info(f"{n.id}: ohmydocs command received for notification {n.id}, but not implemented yet.")
        # Disable until it works well.
        # await run_graph.docs(pull_request_id=issue_or_pull_request_id, db=core_db, docs_db=docs_db)
        return

    if command_name == CommandName.TEST_STEPS and n.subject.type == "PullRequest":
        thinking_comment = create_thinking_comment_for_pr(
            pull_request_id=issue_or_pull_request_id,
            thinking_text=f"{thinking_verb()}...",
        )
        async for step in test_step_pipeline.run(
            issue_or_pull_request_id, core_db, usage_log_id, thinking_comment, should_process_again=should_process_again
        ):
            # we don't wanna print the yield logs
            logger.debug(f"PR #{issue_or_pull_request_id}: {step}")
        return

    await react_comment(n.subject.latest_comment_url, "-1")
    logger.info(f"{n.id}: unknown command, skipping")


def _has_again(comment: IssueComment) -> bool:
    return "again" in comment.body.lower()
