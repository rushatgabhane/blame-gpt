import asyncio
import logging

from libs.github import get_github_client
from libs.helpers import thinking_verb
from libs.sqlite.core.core_sqlite_client import Database as CoreDatabase
from models.enums import CommandName
from services import blame_pipeline, code_review_pipeline, dependency_analysis_pipeline, user_service
from services.command_service import classify_command, has_again_keyword
from services.github.comment_service import create_thinking_comment, react_comment

logger = logging.getLogger(__name__)


async def process_webhook_comment(payload: dict, core_db: CoreDatabase, installation_id: int):
    """Process a GitHub webhook comment event."""
    try:
        repository = payload.get("repository", {})
        repo_id = repository.get("id")

        # Extract comment and issue/PR data
        comment = payload.get("comment") or {}
        comment_body = comment.get("body", "")
        comment_url = comment.get("url", "")

        comment_user = comment.get("user", {})
        user_type = comment_user.get("type", "").lower()
        user_login = comment_user.get("login", "").lower()
        if user_type == "bot" or user_login.endswith("[bot]"):
            return

        issue_or_pr = payload.get("issue") or payload.get("pull_request") or {}
        issue_or_pr_number = issue_or_pr.get("number")
        if not issue_or_pr_number:
            logger.error("No issue or PR number found in webhook payload")
            return
        issue_or_pr_url = issue_or_pr.get("url", "")

        subject_type = "PullRequest" if payload.get("issue") and payload["issue"].get("pull_request") else "Issue"

        logger.info(f"Processing webhook comment for {subject_type} #{issue_or_pr_number}")

        react_task = asyncio.create_task(react_comment(comment_url, "eyes", installation_id))
        command_name = classify_command(comment_body, subject_type)

        # Add user to database
        user_id = user_service.add_user_if_not_exists(
            username=comment_user.get("login", ""),
            email=comment_user.get("email") or "",
            name=comment_user.get("name") or comment_user.get("login", ""),
            avatar_url=comment_user.get("avatar_url", ""),
            core_db=core_db,
        )

        usage_log_id = user_service.add_user_usage_log(
            userID=user_id,
            command_name=command_name,
            comment_url=comment_url,
            output="default output",  # Placeholder, replace later
            issue_or_pull_request_url=issue_or_pr_url,
            core_db=core_db,
            comment_text=comment_body,
        )

        should_process_again = has_again_keyword(comment_body)

        await _run_webhook_command(
            command_name=command_name,
            subject_type=subject_type,
            issue_or_pr_number=issue_or_pr_number,
            repo_id=repo_id,
            core_db=core_db,
            usage_log_id=usage_log_id,
            installation_id=installation_id,
            should_process_again=should_process_again,
        )

        # Wait for react task to complete
        await react_task

    except Exception as e:
        logger.exception(f"error processing webhook comment: {e}")


async def _run_webhook_command(
    command_name,
    subject_type: str,
    issue_or_pr_number: int,
    repo_id: int,
    core_db: CoreDatabase,
    usage_log_id: int | None,
    installation_id: int,
    should_process_again: bool = False,
):
    """Execute the appropriate command based on the webhook comment."""
    if command_name == CommandName.BLAME and subject_type == "Issue":
        # Get GitHub clients for the installation
        gh_client = get_github_client(installation_id)
        repo_client = gh_client.get_repo(repo_id)

        thinking_comment = create_thinking_comment(
            issue_number=issue_or_pr_number, thinking_text=f"{thinking_verb()}...", repo_client=repo_client
        )
        async for step in blame_pipeline.run(
            issue_id=issue_or_pr_number,
            repo_id=repo_id,
            repo_client=repo_client,
            db=core_db,
            usage_log_id=usage_log_id,
            thinking_comment=thinking_comment,
        ):
            logger.debug(f"Blame #{issue_or_pr_number}: {step}")
        return

    if command_name == CommandName.CODE_REVIEW and subject_type == "PullRequest":
        # Get GitHub clients for the installation
        gh_client = get_github_client(installation_id)
        repo_client = gh_client.get_repo(repo_id)

        async for step in code_review_pipeline.run(
            pull_request_id=issue_or_pr_number,
            repo_id=repo_id,
            db=core_db,
            repo_client=repo_client,
            installation_id=installation_id,
            usage_log_id=usage_log_id,
            should_review_again=should_process_again,
        ):
            logger.debug(f"Code review PR #{issue_or_pr_number}: {step}")
        return

    if command_name == CommandName.DEPENDENCY_ANALYSIS and subject_type == "PullRequest":
        # Get GitHub clients for the installation
        gh_client = get_github_client(installation_id)
        repo_client = gh_client.get_repo(repo_id)

        async for step in dependency_analysis_pipeline.run(
            pull_request_id=issue_or_pr_number,
            repo_client=repo_client,
            db=core_db,
            usage_log_id=usage_log_id,
        ):
            logger.debug(f"Dependency analysis PR #{issue_or_pr_number}: {step}")
        return

    logger.info(f"Unknown command {command_name}, skipping")


async def process_webhook_pr_event(payload: dict, core_db: CoreDatabase, installation_id: int):
    """Process a GitHub webhook PR event for automatic dependency analysis."""
    try:
        repository = payload.get("repository", {})
        repo_id = repository.get("id")
        
        pull_request = payload.get("pull_request", {})
        pr_number = pull_request.get("number")
        pr_action = payload.get("action")
        
        if not pr_number:
            logger.error("No PR number found in webhook payload")
            return
            
        # Get PR author info for user tracking
        pr_author = pull_request.get("user", {})
        user_type = pr_author.get("type", "").lower()
        user_login = pr_author.get("login", "").lower()
        
        # Skip bot PRs
        if user_type == "bot" or user_login.endswith("[bot]"):
            logger.info(f"Skipping bot PR #{pr_number}")
            return
        
        logger.info(f"Processing automatic dependency analysis for PR #{pr_number} (action: {pr_action})")
        
        # Add user to database
        user_id = user_service.add_user_if_not_exists(
            username=pr_author.get("login", ""),
            email=pr_author.get("email") or "",
            name=pr_author.get("name") or pr_author.get("login", ""),
            avatar_url=pr_author.get("avatar_url", ""),
            core_db=core_db,
        )
        
        # Log usage for automatic dependency analysis
        usage_log_id = user_service.add_user_usage_log(
            userID=user_id,
            command_name=CommandName.DEPENDENCY_ANALYSIS,
            comment_url="",  # No comment for automatic analysis
            output="automatic dependency analysis",
            issue_or_pull_request_url=pull_request.get("html_url", ""),
            core_db=core_db,
            comment_text=f"automatic analysis on PR {pr_action}",
        )
        
        # Run dependency analysis
        gh_client = get_github_client(installation_id)
        repo_client = gh_client.get_repo(repo_id)
        
        async for step in dependency_analysis_pipeline.run(
            pull_request_id=pr_number,
            repo_client=repo_client,
            db=core_db,
            usage_log_id=usage_log_id,
        ):
            logger.debug(f"Auto dependency analysis PR #{pr_number}: {step}")
            
    except Exception as e:
        logger.exception(f"error processing webhook PR event: {e}")
