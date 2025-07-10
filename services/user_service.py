import logging

from libs.sqlite.core.core_sqlite_client import Database as CoreDatabase

logger = logging.getLogger(__name__)

from models.enums import CommandName


def add_user_if_not_exists(
    username: str,
    email: str,
    name: str,
    avatar_url: str,
    core_db: CoreDatabase,
) -> int:
    try:
        userID = core_db.get_user_id_by_username(username=username)
        if not userID:
            userID = core_db.add_user(username=username, email=email, name=name, avatar_url=avatar_url)

        return userID
    except Exception as e:
        logger.error(f"error adding user {username}: {e}")
        raise e


def add_user_usage_log(
    userID: int,
    command_name: CommandName,
    comment_url: str,
    output: str,
    issue_or_pull_request_url: str,
    core_db: CoreDatabase,
) -> None:
    try:
        core_db.add_usage_log(
            user_id=userID,
            command_name=str(command_name),
            comment_url=comment_url,
            output=output,
            issue_or_pull_request_url=issue_or_pull_request_url,
        )
    except Exception as e:
        logger.error(f"error adding usage log for user {userID} and command {command_name}: {e}")
        raise e
