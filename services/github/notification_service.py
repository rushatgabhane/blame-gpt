import asyncio
import logging
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

logger = logging.getLogger(__name__)

last_checked = datetime.now(UTC)


async def listen_notifications(core_db: CoreDatabase, docs_db: DocsDatabase):
    global last_checked
    previous_last_checked = last_checked

    last_checked = datetime.now(UTC)
    notifications = gh_user.get_notifications(since=previous_last_checked, participating=True)

    if not notifications:
        return

    for n in notifications:
        if not _is_valid_notification(n):
            continue

        latest_comment_url = n.subject.latest_comment_url
        asyncio.create_task(asyncio.to_thread(_react_with_eyes, latest_comment_url))

        comment = _get_comment(latest_comment_url)
        if not comment:
            logger.warning(f"could not fetch comment for notification {n.id}, skipping")
            continue

        command_name = _classify_command(comment.body)

        _run_command(command_name, n, core_db, docs_db)

        _add_usage_log(core_db)
        logger.info(f"user: {comment.user.email}")
        logger.info(f"comment: {comment.body}")

        logger.info(f"notification: {n.subject}")
        logger.info(f"notification url: {latest_comment_url}")


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

    logger.info(f"notification {notification.id} is for {notification.subject.type} {notification.subject.title}")

    return True


def _react_with_eyes(comment_url: str):
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
    try:
        input = command_classifier_prompt.format(
            comment=comment_body,
        )
        response = llmNano.invoke(input)
        classification: CommandClassification = command_classification_parser.invoke(response)
        return CommandName(classification.command_name)
    except Exception as e:
        logger.error(f"failed to classify command for comment {comment_body}: {e}")
        return CommandName.UNKNOWN


def _run_command(command_name: CommandName, notification: Notification, core_db: CoreDatabase, docs_db: DocsDatabase):
    logger.info(f"running command {command_name.value} for notification {notification}")


def _add_usage_log(core_db: CoreDatabase):
    logger.info("saving user usage")
