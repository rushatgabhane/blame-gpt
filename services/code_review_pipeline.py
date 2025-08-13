import asyncio
import logging
from collections.abc import AsyncGenerator

from github.Repository import Repository

from libs.llm import ModelNames, llm
from libs.prompt_templates.code_review import code_review_prompt, line_by_line_review_parser
from libs.sqlite.core.core_sqlite_client import Database
from models.models import LineByLineCodeReview
from services.github.local_repository import LocalRepository
from services.github.pull_request_service import (
    create_pull_request_review,
    format_pr_diffs_for_review,
    get_pull_request_diffs,
)
from services.user_service import track_llm_usage

logger = logging.getLogger(__name__)


async def run(
    pull_request_id: int,
    repo_id: int,
    db: Database,
    repo_client: Repository,
    installation_id: int,
    usage_log_id: int | None = None,
) -> AsyncGenerator[str]:
    try:
        yield f"starting review for PR #{pull_request_id}"
        logger.info(f"starting review for PR #{pull_request_id}")

        pr = repo_client.get_pull(pull_request_id)
        current_commit_sha = pr.head.sha

        last_reviewed_sha = db.get_pull_request_review_sha(pull_request_id, repo_id)
        if last_reviewed_sha == current_commit_sha:
            yield f"PR #{pull_request_id} already reviewed at commit {current_commit_sha}, skipping"
            return

        with LocalRepository(pull_request_id, repo_client, installation_id) as local_repo:
            if local_repo is None:
                yield "error: failed to setup repository"
                return

            gitignore_spec = local_repo.get_gitignore_spec()
            pull_request, pr_diffs = get_pull_request_diffs(
                pull_request_id, repo_client, gitignore_spec, last_reviewed_sha
            )

            formatted_diffs = format_pr_diffs_for_review(pr_diffs)
            prompt = code_review_prompt(
                pr_number=pull_request_id,
                title=pull_request.title,
                description=pull_request.explanation,
                file_diffs=formatted_diffs,
            )

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

            logger.info(f"generated review with {len(review.comments)} comments")
            yield "adding review to PR"

            if not pull_request.commit_sha:
                logger.error(f"Missing commit SHA for PR #{pull_request_id}")
                yield "error: missing commit SHA"
                return

            create_pull_request_review(pull_request_id, review, pull_request.commit_sha, repo_client)
            db.update_pull_request_review(pull_request_id, repo_id, current_commit_sha)

            yield "celebrating! code review is complete"

    except Exception as e:
        logger.exception(f"code review failed for PR #{pull_request_id}: {e}")
        yield f"some error occurred please report it with PR id #{pull_request_id}"
