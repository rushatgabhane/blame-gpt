from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field


class RepositoryOverview(BaseModel):
    overview: str = Field(description="Complete markdown repository overview")


repository_overview_parser = PydanticOutputParser(pydantic_object=RepositoryOverview)

REPOSITORY_OVERVIEW_PROMPT = """Analyze this codebase and provide a comprehensive repository overview.

# Codebase Analysis:
{analysis_summary}

Generate a markdown overview covering:

## 1. Architecture Overview
- Main architectural patterns and design choices
- Key modules and their responsibilities  
- Technology stack

## 2. Components
- Files, classes etc
- Functions and their roles
- Database layers, services, controllers, or similar in different architectures.

## 3. Dependencies & Flow
- How modules depend on each other
- Data flows through the system


Focus on specific insights from the actual code structure provided.

Output format:
{format_instructions}
"""


def format_repository_overview_prompt(code_analysis_data: dict) -> str:
    """Format the repository overview prompt with code analysis data"""
    import json

    # Convert analysis data to formatted JSON
    analysis_json = json.dumps(code_analysis_data, indent=0)

    return REPOSITORY_OVERVIEW_PROMPT.format(
        analysis_summary=analysis_json, format_instructions=repository_overview_parser.get_format_instructions()
    )
