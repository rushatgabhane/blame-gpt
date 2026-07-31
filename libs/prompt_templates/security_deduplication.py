import json

from langchain.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field

from models.models import CodeReviewComment


class FilteredComments(BaseModel):
    filtered_code_review_comments: list[CodeReviewComment] = Field(
        description="Code review comments that should be kept (not duplicates of security comments)"
    )


security_deduplication_parser = PydanticOutputParser(pydantic_object=FilteredComments)


def security_deduplication_prompt(
    code_review_comments: list[CodeReviewComment], security_comments: list[CodeReviewComment]
) -> str:
    """Create prompt to filter duplicate code review comments when security comments exist"""

    template = """
You are filtering code review comments to avoid duplicates with security tool findings.

Given:
1. **Code Review Comments** (from AI code review)
2. **Security Comments** (from automated security tools like Bandit)

Task: Remove code review comments that duplicate or overlap with security comments.

## Guidelines:
- Remove code review comments if they cover the same security issue as an automated security comment
- Remove if they're on the same line or nearby lines (±3 lines) AND address similar security concerns
- Keep code review comments that address different types of issues (code quality, performance, etc.)
- Keep code review comments on different files or significantly different locations
- Security tools are more authoritative for security issues

## Code Review Comments:
{code_review_comments}

## Security Comments (for reference):
{security_comments}

Return a filtered list of code review comments that should be kept in a valid JSON matching the schema:
{format_instructions}
"""

    def format_comments_as_json(comments: list[CodeReviewComment]) -> str:
        if not comments:
            return "[]"

        comments_data = [comment.model_dump(mode="json") for comment in comments]
        return json.dumps(comments_data, separators=(",", ":"))

    formatted_code_review = format_comments_as_json(code_review_comments)
    formatted_security = format_comments_as_json(security_comments)

    prompt = PromptTemplate(
        template=template,
        input_variables=["code_review_comments", "security_comments"],
        partial_variables={"format_instructions": security_deduplication_parser.get_format_instructions()},
    )

    return prompt.format(code_review_comments=formatted_code_review, security_comments=formatted_security)
