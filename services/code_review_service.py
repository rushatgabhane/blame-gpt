import logging

from libs.llm import llmCheap
from libs.prompt_templates.repository_overview import format_repository_overview_prompt, repository_overview_parser
from services.code_index_pipeline import run

logger = logging.getLogger(__name__)


async def generate_code_review():
    project_structure = await run("data/blame-gpt")
    prompt = format_repository_overview_prompt(project_structure.model_dump())

    response = await llmCheap.ainvoke(prompt)
    parsed_response = repository_overview_parser.invoke(response)

    with open("BLAMEGPT.md", "w") as f:
        f.write(parsed_response.overview)

    return parsed_response.overview
