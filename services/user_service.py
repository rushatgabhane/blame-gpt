import logging

from libs.sqlite.core.core_sqlite_client import Database as CoreDatabase
from models.models import UsageLog, User, UserUsageLog

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
        if userID:
            return userID
        
        userID = core_db.add_user(username=username, email=email, name=name, avatar_url=avatar_url)
        if not userID:
            raise ValueError(f"failed to add user: {username}, no ID returned.")

        return userID
    except Exception as e:
        logger.error(f"error adding user: {username}: {e}")
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
            command_name=command_name,
            comment_url=comment_url,
            output=output,
            issue_or_pull_request_url=issue_or_pull_request_url,
        )
    except Exception as e:
        logger.error(f"error adding usage log for user {userID} and command {command_name}: {e}")
        raise e


def get_all_usage_logs_for_all_users(core_db: CoreDatabase) -> list[UserUsageLog]:
    try:
        return core_db.get_all_usage_logs_for_all_users()
    except Exception as e:
        logger.error(f"error fetching usage logs for all users: {e}")
        raise e


def get_all_users(core_db: CoreDatabase) -> list[User]:
    try:
        return core_db.get_all_users()
    except Exception as e:
        logger.error(f"error fetching all users: {e}")
        raise e


def get_usage_log_by_username(
    username: str,
    core_db: CoreDatabase,
) -> list[UsageLog]:
    try:
        userID = core_db.get_user_id_by_username(username=username)
        if not userID:
            logger.warning(f"no user found with username {username}")
            return []

        return core_db.get_usage_logs_by_user_id(userID)
    except Exception as e:
        logger.error(f"error fetching usage logs for user {username}: {e}")
        raise e
