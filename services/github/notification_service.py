import logging
from datetime import UTC, datetime

from libs.github import gh_user

logger = logging.getLogger(__name__)

last_checked = datetime.now(UTC)


def listen_notifications():
    global last_checked
    previous_last_checked = last_checked

    last_checked = datetime.now(UTC)
    notifications = gh_user.get_notifications(since=previous_last_checked, participating=True)

    if not notifications:
        return

    for n in notifications:
        if n.reason != "mention":
            continue

        if n.subject.type != "Issue":
            continue

        logger.info(f"notification: {n.subject}")
        # if n.repository.name != constants.REPO_NAME and n.repository.owner.login != constants.REPO_OWNER:
        #     continue
