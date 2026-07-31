import logging

from libs import bitbucket, constants
from libs.sqlite.core.core_sqlite_client import Database as CoreDatabase
from models.enums import CommandName
from services import user_service
from services.bitbucket import code_review_pipeline
from services.command_service import has_again_keyword

logger = logging.getLogger(__name__)


async def process_bitbucket_comment(payload: dict, core_db: CoreDatabase):
    """Process a Bitbucket pull request comment event forwarded by the Forge app."""
    try:
        workspace = payload.get("workspace", {}).get("uuid", "")
        repo = payload.get("repository", {}).get("uuid", "")
        pull_request_id = payload.get("pullrequest", {}).get("id")
        comment_id = payload.get("comment", {}).get("id")

        if not workspace or not repo or not pull_request_id or not comment_id:
            logger.error("missing fields in bitbucket webhook payload")
            return

        # the Forge event only carries the comment id; fetch the content
        comment = bitbucket.get_pull_request_comment(workspace, repo, pull_request_id, comment_id)
        text = comment.get("content", {}).get("raw", "")

        if constants.USER_TAG.lower() not in text.lower():
            return

        if constants.SIGNATURE in text:
            return

        logger.info(f"Processing bitbucket comment for PR #{pull_request_id}")

        author = comment.get("user", {})
        user_id = user_service.add_user_if_not_exists(
            username=author.get("nickname") or author.get("uuid", ""),
            email="",
            name=author.get("display_name") or author.get("nickname", ""),
            avatar_url=author.get("links", {}).get("avatar", {}).get("href", ""),
            core_db=core_db,
        )

        comment_url = comment.get("links", {}).get("html", {}).get("href", "")
        usage_log_id = user_service.add_user_usage_log(
            userID=user_id,
            command_name=CommandName.CODE_REVIEW,
            comment_url=comment_url,
            output="default output",  # Placeholder, replace later
            issue_or_pull_request_url=comment.get("pullrequest", {}).get("links", {}).get("html", {}).get("href", ""),
            core_db=core_db,
            comment_text=text,
        )

        should_review_again = has_again_keyword(text)

        async for step in code_review_pipeline.run(
            workspace=workspace,
            repo=repo,
            pull_request_id=pull_request_id,
            db=core_db,
            usage_log_id=usage_log_id,
            should_review_again=should_review_again,
        ):
            logger.debug(f"Code review PR #{pull_request_id}: {step}")

    except Exception as e:
        logger.exception(f"error processing bitbucket webhook comment: {e}")
