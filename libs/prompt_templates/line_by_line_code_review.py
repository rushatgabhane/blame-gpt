from langchain.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate

from models.models import LineByLineCodeReview

line_by_line_review_parser = PydanticOutputParser(pydantic_object=LineByLineCodeReview)


def format_line_by_line_review_prompt(pr_data: dict) -> str:
    """Format the line-by-line code review prompt"""

    template = """Please review this pull request and provide feedback on:
- Code quality and best practices
- Potential bugs or issues  
- Performance considerations
- Security concerns
- Test coverage

Be constructive and helpful in your feedback.

Use conventional comments format (https://conventionalcomments.org/):
- praise: Highlight something positive
- nitpick: Trivial preference-based request  
- suggestion: Propose an improvement
- issue: Highlight a specific problem that should be addressed
- todo: Small, tedious, but necessary changes
- question: Ask for clarification or explanation
- thought: Share a non-actionable thought or idea
- chore: Simple mechanical changes
- note: Highlight something important

PR Title: {pr_title}
PR Description: {pr_description}

File Changes:
{file_diffs}

Focus on new or modified lines (marked with +). Provide specific, actionable feedback.
For each comment, specify the exact file and line numbers.

{format_instructions}"""

    prompt = PromptTemplate(
        template=template,
        input_variables=["pr_title", "pr_description", "file_diffs"],
        partial_variables={"format_instructions": line_by_line_review_parser.get_format_instructions()},
    )

    return prompt.format(
        pr_title=pr_data.get("title", ""),
        pr_description=pr_data.get("description", ""),
        file_diffs=pr_data.get("file_diffs", ""),
    )
