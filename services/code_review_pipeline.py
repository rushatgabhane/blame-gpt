import asyncio
import logging
from collections.abc import AsyncGenerator

from libs.github import gh
from libs.llm import ModelNames, llm
from libs.prompt_templates.code_review import code_review_prompt, line_by_line_review_parser
from libs.sqlite.core.core_sqlite_client import Database
from models.models import LineByLineCodeReview
from services.github.local_repository import LocalRepository, with_local_repo
from services.github.pull_request_service import (
    create_pull_request_review,
    format_pr_diffs_for_review,
    get_pull_request_diffs,
)
from services.user_service import track_llm_usage

logger = logging.getLogger(__name__)


@with_local_repo
async def run(
    pull_request_id: int,
    repo_owner: str,
    repo_name: str,
    db: Database,
    usage_log_id: int | None = None,
    local_repo: LocalRepository,
) -> AsyncGenerator[str]:
    try:
        yield f"starting review for PR #{pull_request_id} in {repo_owner}/{repo_name}"

        repo = gh.get_repo(f"{repo_owner}/{repo_name}")

        gitignore_spec = local_repo.get_gitignore_spec()
        pull_request, pr_diffs = get_pull_request_diffs(pull_request_id, repo, gitignore_spec)
        logger.info(f"Retrieved PR data and {len(pr_diffs)} file diffs with gitignore filtering")

        formatted_diffs = format_pr_diffs_for_review(pr_diffs)
        pr_data = {"title": pull_request.title, "description": pull_request.explanation, "file_diffs": formatted_diffs}
        prompt = code_review_prompt(pr_data)
        logger.info(f"Generated prompt with {len(prompt)} characters")

        llm_task = asyncio.create_task(llm.ainvoke(prompt))

        while not llm_task.done():
            await asyncio.sleep(20)
            yield "generating code review... this might take a minute."

        response = await llm_task
        track_llm_usage(db, usage_log_id, response, ModelNames.GPT_5)

        parsed_response = line_by_line_review_parser.invoke(response)

        review = LineByLineCodeReview(
            pr_number=pull_request_id,
            comments=parsed_response.comments,
            code_overview=parsed_response.code_overview,
            files_reviewed=[diff.filename for diff in pr_diffs if diff.patch],
        )

        logger.info(f"Generated review with {len(review.comments)} comments")
        yield "adding review to PR"

        if not pull_request.commit_sha:
            logger.error(f"Missing commit SHA for PR #{pull_request_id}")
            yield "error: missing commit SHA"
            return

        create_pull_request_review(pull_request_id, review, pull_request.commit_sha, repo)

        yield "celebrating! code review is complete"

    except Exception as e:
        logger.exception(f"code review failed for PR #{pull_request_id}: {e}")
        yield f"some error occurred please report it with PR id #{pull_request_id}"
