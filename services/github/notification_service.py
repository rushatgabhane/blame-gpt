import asyncio
import logging
from datetime import UTC, datetime

from github.IssueComment import IssueComment
from github.Notification import Notification

from libs import constants
from libs.github import gh_user

logger = logging.getLogger(__name__)

last_checked = datetime.now(UTC)


async def listen_notifications():
    global last_checked
    previous_last_checked = last_checked

    last_checked = datetime.now(UTC)
    notifications = gh_user.get_notifications(since=previous_last_checked, participating=True)

    if not notifications:
        return

    for n in notifications:
        if not _is_valid_notification(n):
            continue

        commentID = int(n.subject.latest_comment_url.split("/")[-1])
        commentURL = n.subject.latest_comment_url
        asyncio.create_task(asyncio.to_thread(_react_with_eyes, commentID))

        comment = _get_comment(commentURL)
        logger.info(f"comment: {comment}")

        logger.info(f"notification: {n.subject}")
        logger.info(f"notification url: {commentURL}")


def _is_valid_notification(notification: Notification) -> bool:
    if notification.reason != "mention":
        return False

    if notification.subject.type != "Issue":
        return False

    if (
        notification.repository.name != constants.REPO_NAME
        and notification.repository.owner.login != constants.REPO_OWNER
    ):
        return False

    if not notification.subject.latest_comment_url:
        logger.warning(f"notification {notification.id} has no latest comment URL, skipping")
        return False

    return True


def _react_with_eyes(commentID: int):
    try:
        gh_user._requester.requestJsonAndCheck(
            verb="POST",
            url=f"https://api.github.com/repos/{constants.REPO_OWNER}/{constants.REPO_NAME}/issues/comments/{commentID}/reactions",
            input={"content": "eyes"},
        )
    except Exception as e:
        logger.error(f"failed to react with eyes on comment {commentID}: {e}")


def _get_comment(commentURL: str) -> IssueComment | None:
    try:
        _headers, data = gh_user._requester.requestJsonAndCheck(
            verb="GET",
            url=commentURL,
        )
        return IssueComment(requester=gh_user._requester, headers=_headers, attributes=data, completed=True)
    except Exception as e:
        logger.error(f"failed to get comment {commentURL}: {e}")
        return None
