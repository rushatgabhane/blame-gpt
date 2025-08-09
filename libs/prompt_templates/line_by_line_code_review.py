"""Line-by-line code review prompt template"""


from langchain.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field


class CodeReviewComment(BaseModel):
    """Individual code review comment"""
    
    file: str = Field(description="The file path where the comment applies")
    start_line: int = Field(description="The starting line number for the comment")
    end_line: int = Field(description="The ending line number for the comment")
    content: str = Field(description="The review comment content")
    label: str = Field(description="Conventional comment label: 'praise', 'nitpick', 'suggestion', 'issue', 'todo', 'question', 'thought', 'chore', 'note'")
    category: str = Field(description="Comment category: 'bug', 'security', 'performance', 'quality', 'test'")


class LineByLineCodeReview(BaseModel):
    """Complete line-by-line code review"""
    
    comments: list[CodeReviewComment] = Field(description="List of review comments")
    overall_score: int = Field(description="Overall code quality score from 1-10")
    summary: str = Field(description="Brief summary of the review findings")


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
        partial_variables={"format_instructions": line_by_line_review_parser.get_format_instructions()}
    )
    
    return prompt.format(
        pr_title=pr_data.get("title", ""),
        pr_description=pr_data.get("description", ""),
        file_diffs=pr_data.get("file_diffs", "")
    )