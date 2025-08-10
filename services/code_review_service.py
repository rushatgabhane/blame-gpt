import logging
from collections.abc import AsyncGenerator

from libs.llm import ModelNames, llm
from libs.prompt_templates.code_review import code_review_prompt, line_by_line_review_parser
from libs.sqlite.core.core_sqlite_client import Database
from models.models import LineByLineCodeReview
from services.github.pull_request_service import (
    create_pull_request_review,
    format_pr_diffs_for_review,
    get_pull_request_diffs,
)
from services.user_service import track_llm_usage

logger = logging.getLogger(__name__)


async def run_line_by_line_review(
    pull_request_id: int, db: Database, usage_log_id: int | None = None
) -> AsyncGenerator[str]:
    try:
        yield f"starting line-by-line review for PR #{pull_request_id}..."

        yield "fetching pull request data and file diffs..."
        pull_request, pr_diffs = get_pull_request_diffs(pull_request_id)
        logger.info(f"Retrieved PR data and {len(pr_diffs)} file diffs")

        yield f"analyzing {len(pr_diffs)} changed files..."

        formatted_diffs = format_pr_diffs_for_review(pr_diffs)

        pr_data = {"title": pull_request.title, "description": pull_request.explaination, "file_diffs": formatted_diffs}

        yield "generating review using AI..."

        prompt = code_review_prompt(pr_data)
        logger.info(f"Generated prompt with {len(prompt)} characters")

        response = await llm.ainvoke(prompt)

        track_llm_usage(db, usage_log_id, response, ModelNames.GPT_5_MINI)

        yield "parsing AI response..."
        parsed_response = line_by_line_review_parser.invoke(response)

        review = LineByLineCodeReview(
            pr_number=pull_request_id,
            comments=parsed_response.comments,
            code_overview=parsed_response.code_overview,
            files_reviewed=[diff.filename for diff in pr_diffs if diff.patch],
        )

        logger.info(f"Generated review with {len(review.comments)} comments")
        yield "adding review comment to PR"

        create_pull_request_review(pull_request_id, review)

        yield "review complete!"

    except Exception as e:
        logger.exception(f"Line-by-line review failed for PR #{pull_request_id}: {e}")
        yield f"error: {str(e)}"
