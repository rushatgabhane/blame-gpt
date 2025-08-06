from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field


class ImportantFiles(BaseModel):
    files: list[str] = Field(description="List of important file paths (relative from root)")


important_files_parser = PydanticOutputParser(pydantic_object=ImportantFiles)

IDENTIFY_IMPORTANT_FILES_PROMPT = """
Analyze this directory structure and identify the most architecturally important files.

Focus on:
- Entry points (main.py, app.py, etc.)
- Controllers/routers (handling HTTP requests), incoming events from queue, brokers, MQTT, webhook, cron triggers and so on.
- Core services and business logic
- Models and data structures
- Important utilities/libraries

Directory structure:
{file_tree}

Only include files that exist in the structure above. 
Return the top **50** most important files.

{format_instructions}
"""


def format_identify_important_files_prompt(file_tree: str) -> str:
    return IDENTIFY_IMPORTANT_FILES_PROMPT.format(
        file_tree=file_tree, format_instructions=important_files_parser.get_format_instructions()
    )
