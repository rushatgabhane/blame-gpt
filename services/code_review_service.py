import logging

from libs.llm import llmCheap
from libs.prompt_templates.repository_overview import format_repository_overview_prompt, repository_overview_parser
from services.code_index_pipeline import run

logger = logging.getLogger(__name__)


async def generate_code_review():
    try:
        logger.info("Starting project structure analysis")
        project_structure = await run("data/blame-gpt")
        logger.info(f"Project structure generated with {project_structure.total_files} files")

        # Include only key component relationships
        filtered_call_graph = _filter_call_graph_for_key_components(
            project_structure.call_graph, project_structure.key_components
        )

        summary_data = {
            "name": project_structure.name,
            "total_files": project_structure.total_files,
            "languages": project_structure.languages,
            "architecture_summary": project_structure.architecture_summary,
            "key_components": project_structure.key_components,
            "directory_structure": project_structure.file_tree,
            "call_graph": filtered_call_graph,
        }

        prompt = format_repository_overview_prompt(summary_data)
        logger.info(f"Prompt length: {len(prompt)} characters")

        response = await llmCheap.ainvoke(prompt)

        token_usage = response.response_metadata["token_usage"]
        logger.info(
            f"Token usage - Input: {token_usage.get('prompt_tokens', 'N/A')}, "
            f"Output: {token_usage.get('completion_tokens', 'N/A')}, "
            f"Total: {token_usage.get('total_tokens', 'N/A')}"
        )

        parsed_response = repository_overview_parser.invoke(response)

        logger.info("Writing overview to BLAMEGPT.md")
        with open("BLAMEGPT.md", "w") as f:
            f.write(parsed_response.overview)

        return parsed_response.overview

    except Exception as e:
        logger.error(f"Code review generation failed: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        raise


def _filter_call_graph_for_key_components(call_graph: dict, key_components: list[dict]) -> dict:
    """Filter call graph to only include entities from key component files"""
    key_files = {comp["file"] for comp in key_components}
    filtered_graph = {}

    for entity_id, calls in call_graph.items():
        file_path = entity_id.split(":")[0]
        if file_path in key_files:
            filtered_graph[entity_id] = calls

    return filtered_graph
