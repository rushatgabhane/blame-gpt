import asyncio
import logging
from collections.abc import AsyncGenerator

from libs import bitbucket
from libs.llm import ModelNames, llm
from libs.prompt_templates.code_review import code_review_prompt, line_by_line_review_parser
from libs.sqlite.core.core_sqlite_client import Database
from models.models import CodeReviewComment, LineByLineCodeReview
from services.bitbucket.local_repository import LocalRepository
from services.bitbucket.pull_request_service import create_pull_request_review, get_pull_request_diffs
from services.diff_service import format_pr_diffs_for_review
from services.review_service import filter_duplicate_security_comments, security_findings_to_comments
from services.security_service import run_security_analysis
from services.user_service import track_llm_usage

logger = logging.getLogger(__name__)


async def run(
    workspace: str,
    repo: str,
    pull_request_id: int,
    db: Database,
    usage_log_id: int | None = None,
    should_review_again: bool = False,
) -> AsyncGenerator[str]:
    """Review a Bitbucket pull request. `workspace` and `repo` are UUIDs from the Forge event;
    `repo` doubles as the repo_id for review tracking."""
    try:
        yield f"starting review for PR #{pull_request_id}"
        logger.info(f"starting review for bitbucket PR #{pull_request_id}")

        pull_request = bitbucket.get_pull_request(workspace, repo, pull_request_id)

        with LocalRepository(pull_request) as local_repo:
            if local_repo is None:
                yield "error: failed to setup repository"
                return

            gitignore_spec = local_repo.get_gitignore_spec()
            last_reviewed_sha = (
                db.get_pull_request_review_sha(pull_request_id, repo) if not should_review_again else None
            )

            commit_sha = local_repo.head_sha()
            if not commit_sha:
                yield "error: could not resolve PR head commit"
                return

            if not should_review_again and last_reviewed_sha == commit_sha:
                yield f"PR #{pull_request_id} already reviewed at commit {commit_sha}, skipping"
                return

            # incremental review: diff only the commits since the last review;
            # falls back to the full PR when the old commit is gone (e.g. force push)
            incremental_diff = local_repo.get_incremental_diff(last_reviewed_sha) if last_reviewed_sha else None
            since_sha = last_reviewed_sha if incremental_diff is not None else None

            model, pr_diffs = get_pull_request_diffs(
                workspace, repo, pull_request, gitignore_spec, incremental_diff=incremental_diff
            )

            formatted_diffs = format_pr_diffs_for_review(pr_diffs)
            prompt = code_review_prompt(
                pr_number=pull_request_id,
                title=model.title,
                description=model.explanation,
                file_diffs=formatted_diffs.diff,
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

            create_pull_request_review(workspace, repo, pull_request_id, review, last_reviewed_sha=since_sha)
            db.update_pull_request_review(pull_request_id, repo, commit_sha)

            yield "celebrating! code review is complete"

    except Exception as e:
        logger.exception(f"bitbucket code review failed for PR #{pull_request_id}: {e}")
        yield f"some error occurred please report it with PR id #{pull_request_id}"
