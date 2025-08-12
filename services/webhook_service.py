import asyncio
import logging
import threading

from libs.github import get_github_client
from libs.helpers import thinking_verb
from libs.sqlite.core.core_sqlite_client import Database as CoreDatabase
from libs.sqlite.docs.docs_sqlite_client import Database as DocsDatabase
from models.enums import CommandName
from services import blame_pipeline, code_review_pipeline, user_service
from services.command_service import classify_command, has_again_keyword
from services.docs_service import run_graph
from services.github.comment_service import create_thinking_comment, create_thinking_comment_for_pr, react_comment
from services.test_step import test_step_pipeline

logger = logging.getLogger(__name__)


async def process_webhook_comment(payload: dict, core_db: CoreDatabase, docs_db: DocsDatabase, installation_id: int):
    """Process a GitHub webhook comment event."""
    try:
        repository = payload.get("repository", {})
        repo_owner = repository.get("owner", {}).get("login", "")
        repo_name = repository.get("name", "")

        # Extract comment and issue/PR data
        comment = payload.get("comment") or {}
        comment_body = comment.get("body", "")
        comment_url = comment.get("url", "")

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
        comment_user = comment.get("user", {})
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
            repo_owner=repo_owner,
            repo_name=repo_name,
            core_db=core_db,
            docs_db=docs_db,
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
    repo_owner: str,
    repo_name: str,
    core_db: CoreDatabase,
    docs_db: DocsDatabase,
    usage_log_id: int | None,
    installation_id: int,
    should_process_again: bool = False,
):
    """Execute the appropriate command based on the webhook comment."""
    if command_name == CommandName.BLAME and subject_type == "Issue":
        # Get GitHub clients for the installation
        gh_client = get_github_client(installation_id)
        repo_client = gh_client.get_repo(f"{repo_owner}/{repo_name}")

        thinking_comment = create_thinking_comment(
            issue_number=issue_or_pr_number, thinking_text=f"{thinking_verb()}...", repo_client=repo_client
        )
        async for step in blame_pipeline.run(
            issue_id=issue_or_pr_number,
            repo_client=repo_client,
            db=core_db,
            usage_log_id=usage_log_id,
            thinking_comment=thinking_comment,
        ):
            logger.debug(f"Blame #{issue_or_pr_number}: {step}")
        return

    if command_name == CommandName.OHMYDOCS:
        async for step in _docs_with_progress_webhook(
            issue_or_pr_number, repo_owner, repo_name, core_db, docs_db, installation_id, usage_log_id
        ):
            logger.debug(f"Docs #{issue_or_pr_number}: {step}")
        return

    if command_name == CommandName.TEST_STEPS and subject_type == "PullRequest":
        # Get GitHub clients for the installation
        gh_client = get_github_client(installation_id)
        repo_client = gh_client.get_repo(f"{repo_owner}/{repo_name}")

        thinking_comment = create_thinking_comment_for_pr(
            pull_request_id=issue_or_pr_number,
            thinking_text=f"{thinking_verb()}... <img src='https://github.com/user-attachments/assets/3689d0a2-6ccb-4431-8cd4-3c433c916d4a' height=16>",
            repo_client=repo_client,
        )
        async for step in test_step_pipeline.run(
            issue_or_pr_number,
            repo_client,
            core_db,
            usage_log_id,
            thinking_comment,
            should_process_again=should_process_again,
        ):
            logger.debug(f"Test steps PR #{issue_or_pr_number}: {step}")
        return

    if command_name == CommandName.CODE_REVIEW and subject_type == "PullRequest":
        # Get GitHub clients for the installation
        gh_client = get_github_client(installation_id)
        repo_client = gh_client.get_repo(f"{repo_owner}/{repo_name}")

        async for step in code_review_pipeline.run(
            pull_request_id=issue_or_pr_number,
            repo_owner=repo_owner,
            repo_name=repo_name,
            db=core_db,
            repo_client=repo_client,
            installation_id=installation_id,
            usage_log_id=usage_log_id,
        ):
            logger.debug(f"Code review PR #{issue_or_pr_number}: {step}")
        return

    logger.info(f"Unknown command {command_name}, skipping")


async def _docs_with_progress_webhook(
    pull_request_id: int,
    repo_owner: str,
    repo_name: str,
    core_db: CoreDatabase,
    docs_db: DocsDatabase,
    installation_id: int,
    usage_log_id: int | None,
):
    """Handle docs command with progress updates."""

    result = []

    def run_docs():
        result.append(
            run_graph.docs(pull_request_id, core_db, docs_db, installation_id, repo_owner, repo_name, usage_log_id)
        )

    thread = threading.Thread(target=run_docs)
    thread.start()

    # Keep yielding to prevent worker timeout
    while thread.is_alive():
        yield "processing..."
        await asyncio.sleep(10)

    thread.join()
