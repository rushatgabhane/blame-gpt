import asyncio
import logging
from collections.abc import AsyncGenerator

from github.Repository import Repository

from libs.llm import ModelNames, llm
from libs.prompt_templates.code_review import code_review_prompt, line_by_line_review_parser
from libs.sqlite.core.core_sqlite_client import Database
from models.models import CodeReviewComment, LineByLineCodeReview
from services.diff_service import format_pr_diffs_for_review
from services.github.local_repository import LocalRepository
from services.github.pull_request_service import create_pull_request_review, get_pull_request_diffs
from services.review_service import filter_duplicate_security_comments, security_findings_to_comments
from services.security_service import run_security_analysis
from services.user_service import track_llm_usage

logger = logging.getLogger(__name__)


async def run(
    pull_request_id: int,
    repo_id: int,
    db: Database,
    repo_client: Repository,
    installation_id: int,
    usage_log_id: int | None = None,
    should_review_again: bool = False,
) -> AsyncGenerator[str]:
    try:
        yield f"starting review for PR #{pull_request_id}"
        logger.info(f"starting review for PR #{pull_request_id}")

        with LocalRepository(pull_request_id, repo_client, installation_id) as local_repo:
            if local_repo is None:
                yield "error: failed to setup repository"
                return

            gitignore_spec = local_repo.get_gitignore_spec()
            last_reviewed_sha = (
                db.get_pull_request_review_sha(pull_request_id, repo_id) if not should_review_again else None
            )

            pull_request, pr_diffs = get_pull_request_diffs(
                pull_request_id, repo_client, gitignore_spec, last_reviewed_sha
            )

            if not pull_request.commit_sha:
                return

            if not should_review_again and last_reviewed_sha == pull_request.commit_sha:
                yield f"PR #{pull_request_id} already reviewed at commit {pull_request.commit_sha}, skipping"
                return

            formatted_diffs = format_pr_diffs_for_review(pr_diffs)
            custom_context = local_repo.read_blamegpt_context()
            prompt = code_review_prompt(
                pr_number=pull_request_id,
                title=pull_request.title,
                description=pull_request.explanation,
                file_diffs=formatted_diffs.diff,
                custom_context=custom_context,
            )

            llm_task = asyncio.create_task(llm.ainvoke(prompt))
            security_task = asyncio.create_task(
                run_security_analysis(local_repo.worktree_path, pr_diffs, formatted_diffs.file_line_number_changed_map)
            )

            while not llm_task.done() or not security_task.done():
                await asyncio.sleep(10)
                yield "generating code review..."

            response = await llm_task
            security_findings = await security_task

            track_llm_usage(db, usage_log_id, response, ModelNames.GPT_5)

            code_review_response: LineByLineCodeReview = line_by_line_review_parser.invoke(response)
            security_comments: list[CodeReviewComment] = security_findings_to_comments(security_findings)

            filtered_code_review_comments = await filter_duplicate_security_comments(
                code_review_response.comments, security_comments, db, usage_log_id
            )
            all_comments = security_comments + filtered_code_review_comments

            review = LineByLineCodeReview(
                pr_number=pull_request_id,
                comments=all_comments,
                code_overview=code_review_response.code_overview,
                files_reviewed=[diff.filename for diff in pr_diffs if diff.patch],
            )

            logger.info(f"found {len(review.comments)} review comments")
            logger.info(f"found {len(security_comments)} security comments")
            yield "adding review to PR"

            if not pull_request.commit_sha:
                logger.error(f"Missing commit SHA for PR #{pull_request_id}")
                yield "error: missing commit SHA"
                return

            create_pull_request_review(pull_request_id, review, pull_request.commit_sha, repo_client, last_reviewed_sha)
            db.update_pull_request_review(pull_request_id, repo_id, pull_request.commit_sha)

            yield "celebrating! code review is complete"

    except Exception as e:
        logger.exception(f"code review failed for PR #{pull_request_id}: {e}")
        yield f"some error occurred please report it with PR id #{pull_request_id}"
