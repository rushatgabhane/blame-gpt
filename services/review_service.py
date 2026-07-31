import logging

from libs.llm import ModelNames, llmCheap
from libs.prompt_templates.security_deduplication import security_deduplication_parser, security_deduplication_prompt
from libs.sqlite.core.core_sqlite_client import Database
from models.enums import CodeReviewCommentType
from models.models import CodeReviewComment, SecurityFinding
from services.user_service import track_llm_usage

logger = logging.getLogger(__name__)


def is_allowed_comment_type(comment_type: CodeReviewCommentType) -> bool:
    return (
        comment_type == CodeReviewCommentType.SECURITY
        or comment_type == CodeReviewCommentType.ISSUE
        or comment_type == CodeReviewCommentType.SUGGESTION
    )


def security_findings_to_comments(findings: list[SecurityFinding]) -> list[CodeReviewComment]:
    comments = []
    for finding in findings:
        comment = CodeReviewComment(
            file=finding.file_path,
            line=finding.line,
            start_line=finding.start_line,
            content=f"{finding.severity.value.upper()}: {finding.description} (Rule: {finding.tool} {finding.rule_id})",
            label=CodeReviewCommentType.SECURITY,
        )
        comments.append(comment)
    return comments


async def filter_duplicate_security_comments(
    code_comments: list[CodeReviewComment],
    security_comments: list[CodeReviewComment],
    db: Database,
    usage_log_id: int | None,
) -> list[CodeReviewComment]:
    if not security_comments or not code_comments:
        return code_comments

    dedup_prompt = security_deduplication_prompt(code_comments, security_comments)
    dedup_response = await llmCheap.ainvoke(dedup_prompt)
    track_llm_usage(db, usage_log_id, dedup_response, ModelNames.GPT_5_MINI)

    filtered_result = security_deduplication_parser.invoke(dedup_response)
    return filtered_result.filtered_code_review_comments
