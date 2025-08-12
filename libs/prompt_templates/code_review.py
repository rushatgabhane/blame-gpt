from langchain.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate

from models.enums import CodeReviewCommentType
from models.models import LineByLineCodeReview

line_by_line_review_parser = PydanticOutputParser(pydantic_object=LineByLineCodeReview)


def code_review_prompt(pr_data: dict) -> str:
    """Format the line-by-line code review prompt"""

    template = """
You are a senior software engineer reviewing your coworker's pull request. Think really hard.

**PR Title:** {pr_title}
**PR Description:** {pr_description}

### Focus your review on
- Code quality and best practices
- Potential bugs or issues
- Performance considerations
- Security concerns
- Test coverage

### Review Guidelines
- MUST be constructive and helpful in your feedback
- Focus only on the most important issues - prioritize quality over quantity
- MUST NOT make any comments about code format, whitespace or documentation
- MUST NOT make any comments about import statements
- MUST NOT make any assumptions about code you don't have in your context
- Be selective - avoid commenting on minor style preferences or trivial issues
- Add comment only on lines with "+" additions

### Comment Types
Use conventional comments format (https://conventionalcomments.org/):
Set the label field using exact values from this list:
<label_type_list>
{comment_types}
</label_type_list>

## Output Format Requirements

### Comment Formatting:
- Set the label only in the "label" field
- The content field should contain ONLY the actual feedback text, without any prefixes
- MUST NOT start content with "Note:", "Suggestion:", "Issue:", etc.

### Line Number Rules:
- Use the line numbers shown as prefixes in the diff (e.g. if you see "109 +    code", use line number 109)
- These line numbers correspond to the actual file line numbers, not sequential diff line numbers
- For SINGLE-LINE comments: Only set the "line" field, leave "start_line" as null
- For MULTI-LINE comments: Set both "start_line" (first line) and "line" (last line)
- Line ranges are INCLUSIVE (both start and end lines are included in the comment scope)
- Only comment on lines with changes (marked with + or -)

## File Changes
{file_diffs}

Focus on new code (lines marked with +) and provide specific, actionable feedback only on lines with "+" additions.

Return the result in this JSON format:
{format_instructions}

"""

    # Generate comment types list from enum
    comment_types = "\n".join([f"- {ct.value}: {ct.description()}" for ct in CodeReviewCommentType])

    prompt = PromptTemplate(
        template=template,
        input_variables=["pr_title", "pr_description", "file_diffs"],
        partial_variables={
            "format_instructions": line_by_line_review_parser.get_format_instructions(),
            "comment_types": comment_types,
        },
    )

    return prompt.format(
        pr_title=pr_data.get("title", ""),
        pr_description=pr_data.get("description", ""),
        file_diffs=pr_data.get("file_diffs", ""),
    )
