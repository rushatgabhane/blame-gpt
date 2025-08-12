import logging

from libs.llm import LLM_PRICING
from libs.sqlite.core.core_sqlite_client import Database as CoreDatabase
from models.enums import CommandName
from models.models import UsageLog, User, UserUsageLog

logger = logging.getLogger(__name__)


def track_llm_usage(core_db: CoreDatabase, usage_log_id: int | None, llm_response, model_name: str):
    """
    Ideally this method should be agnostic to LLM model.
    Tested with OpenAI models only at the moment.
    Track LLM usage tokens and cost.
    """
    if usage_log_id is None:
        return

    try:
        pricing = LLM_PRICING.get(model_name)
        if not pricing:
            logger.warning(f"no pricing info found for model: {model_name}")
            return

        token_usage = getattr(llm_response, "usage_metadata", None)
        if token_usage:
            input_tokens = token_usage.get("input_tokens", 0)
            output_tokens = token_usage.get("output_tokens", 0)
            reasoning_tokens = token_usage.get("output_token_details", {}).get("reasoning", 0)

            # Because input and output tokens are priced differently, we calculate a weighted total
            input_weight = pricing.input_price_per_token / pricing.output_price_per_token
            weighted_total_tokens = int(input_tokens * input_weight) + output_tokens + reasoning_tokens

            input_cost_usd = input_tokens * pricing.input_price_per_token
            output_cost_usd = output_tokens * pricing.output_price_per_token
            reasoning_cost_usd = reasoning_tokens * pricing.reasoning_price_per_token

            total_cost_usd = input_cost_usd + output_cost_usd + reasoning_cost_usd
            # Store cost in 0.001 USD units (1 = 0.001 USD)
            cost_usd_thousandths = max(1, int(total_cost_usd * 1000))  # Minimum 0.001 USD

            core_db.add_llm_call(
                usage_log_id=usage_log_id,
                llm_model=model_name,
                tokens_used=weighted_total_tokens,
                cost_usd_thousandths=cost_usd_thousandths,
            )
    except Exception as e:
        logger.error(f"Error tracking LLM usage: {e}")


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
    comment_text: str,
) -> int | None:
    try:
        return core_db.add_usage_log(
            user_id=userID,
            command_name=command_name,
            comment_url=comment_url,
            output=output,
            issue_or_pull_request_url=issue_or_pull_request_url,
            comment_text=comment_text,
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
