import asyncio
import logging
import os
from datetime import UTC, datetime

from github.IssueComment import IssueComment
from github.Notification import Notification

from libs import constants
from libs.github import gh_user
from libs.llm import llmNano
from libs.prompt_templates.command_classification import command_classification_parser, command_classifier_prompt
from libs.sqlite.core.core_sqlite_client import Database as CoreDatabase
from libs.sqlite.docs.docs_sqlite_client import Database as DocsDatabase
from models.enums import CommandName
from models.models import CommandClassification
from services import blame_pipeline, user_service

logger = logging.getLogger(__name__)


async def listen_notifications(last_checked: datetime, core_db: CoreDatabase, docs_db: DocsDatabase):
    previous_last_checked = last_checked

    last_checked = datetime.now(UTC)
    notifications = gh_user.get_notifications(since=previous_last_checked, participating=True)

    if not notifications:
        return

    for n in notifications:
        if not _is_valid_notification(n):
            continue
        asyncio.create_task(process_notification(n, core_db, docs_db))


async def process_notification(n: Notification, core_db: CoreDatabase, docs_db: DocsDatabase):
    try:
        latest_comment_url = n.subject.latest_comment_url
        asyncio.create_task(asyncio.to_thread(_react_with_eyes, latest_comment_url))

        comment = _get_comment(latest_comment_url)
        if not comment:
            logger.warning(f"could not fetch comment for notification {n.id}, skipping")
            return

        command_name = _classify_command(comment.body)
        await _run_command(command_name, n, core_db, docs_db)

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
        )
    except Exception as e:
        logger.error(f"error processing notification : {n} : {e}")


def _is_valid_notification(notification: Notification) -> bool:
    if notification.reason != "mention":
        return False

    if notification.subject.type != "Issue" and notification.subject.type != "PullRequest":
        return False

    if (
        notification.repository.name != constants.REPO_NAME
        and notification.repository.owner.login != constants.REPO_OWNER
    ):
        logger.warning(f"notification {notification.id} is from {notification.repository}, skipping")
        return False

    if not notification.subject.latest_comment_url:
        logger.warning(f"notification {notification.id} has no latest comment URL, skipping")
        return False

    return True


def _react_with_eyes(comment_url: str):
    if os.getenv("ENVIRONMENT") != "production":
        logger.info(f"skipping reaction to comment {comment_url} in non production environment")
        return

    try:
        gh_user._requester.requestJsonAndCheck(
            verb="POST",
            url=f"{comment_url}/reactions",
            input={"content": "eyes"},
        )
    except Exception as e:
        logger.error(f"failed to react with eyes on comment {comment_url}/reactions: {e}")


def _get_comment(comment_url: str) -> IssueComment | None:
    try:
        _headers, data = gh_user._requester.requestJsonAndCheck(
            verb="GET",
            url=comment_url,
        )
        return IssueComment(requester=gh_user._requester, headers=_headers, attributes=data, completed=True)
    except Exception as e:
        logger.error(f"failed to get comment {comment_url}: {e}")
        return None


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


async def _run_command(
    command_name: CommandName, notification: Notification, core_db: CoreDatabase, docs_db: DocsDatabase
):
    issue_or_pull_request_url = notification.subject.url
    issue_or_pull_request_id = int(issue_or_pull_request_url.split("/")[-1])

    if command_name == CommandName.BLAME and notification.subject.type == "Issue":
        async for step in blame_pipeline.run(issue_id=issue_or_pull_request_id, db=core_db):
            logger.info(f"#{issue_or_pull_request_id} {step}")
        return

    if command_name == CommandName.OHMYDOCS:
        # Disable until it works well.
        # await run_graph.docs(pull_request_id=issue_or_pull_request_id, db=core_db, docs_db=docs_db)
        return

    if command_name == CommandName.TEST_STEPS:
        # Disable until it works well.
        # async for step in test_steps_pipeline.run(pull_request_id=issue_or_pull_request_id, db=core_db):
        #     logger.info(f"#{issue_or_pull_request_id}: {step}")
        return

    if command_name == CommandName.UNKNOWN:
        logger.info(f"unknown command for notification {notification.id}, skipping")
        return
