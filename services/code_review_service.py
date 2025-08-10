import json
import logging
from collections.abc import AsyncGenerator

from libs.llm import ModelNames, llm, llmCheap
from libs.prompt_templates.code_review import code_review_prompt, line_by_line_review_parser
from libs.prompt_templates.repository_overview import format_repository_overview_prompt, repository_overview_parser
from libs.sqlite.core.core_sqlite_client import Database
from models.models import LineByLineCodeReview
from services.code_index_pipeline import run
from services.github.pull_request_service import (
    create_pull_request_review,
    format_pr_diffs_for_review,
    get_pull_request_diffs,
)
from services.user_service import track_llm_usage

logger = logging.getLogger(__name__)


async def generate_code_review():
    try:
        logger.info("Starting project structure analysis")
        codebase_path = "data/sentry"
        project_structure = await run(codebase_path)
        logger.info(f"Project structure generated with {project_structure.total_files} files")

        # Include only key component relationships
        filtered_call_graph = _filter_call_graph_for_key_components(
            project_structure.call_graph, project_structure.key_components
        )

        # Filter file analyses to only include entities that are in the filtered call graph
        filtered_file_analyses = _filter_file_analyses_for_call_graph(
            project_structure.file_analyses, filtered_call_graph
        )

        summary_data = {
            # "project_structure": project_structure.model_dump(),
            "name": project_structure.name,
            "total_files": project_structure.total_files,
            "languages": project_structure.languages,
            "architecture_summary": project_structure.architecture_summary,
            "key_components": project_structure.key_components,
            "file_analyses": [analysis.model_dump() for analysis in filtered_file_analyses],
            "call_graph": filtered_call_graph,
        }

        # Optimize data before sending to LLM
        optimized_data = _optimize_data_for_llm(summary_data, codebase_path)

        with open("optimized_data.json", "w") as f:
            json.dump(optimized_data, f, indent=2, default=str)

        prompt = format_repository_overview_prompt(optimized_data)
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
        raise


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
            code_overview=parsed_response.summary,
            files_reviewed=[diff.filename for diff in pr_diffs if diff.patch],
        )

        logger.info(f"Generated review with {len(review.comments)} comments")
        yield "adding review comment to PR"

        create_pull_request_review(pull_request_id, review)

        yield "review complete!"

    except Exception as e:
        logger.exception(f"Line-by-line review failed for PR #{pull_request_id}: {e}")
        yield f"error: {str(e)}"


def _filter_call_graph_for_key_components(call_graph: dict, key_components: list[dict]) -> dict:
    """Filter call graph to only include entities from key component files"""
    key_files = {comp["file"] for comp in key_components}
    filtered_graph = {}

    for entity_id, calls in call_graph.items():
        file_path = entity_id.split(":")[0]
        if file_path in key_files:
            filtered_graph[entity_id] = calls

    return filtered_graph


def _filter_file_analyses_for_call_graph(file_analyses: list, call_graph: dict) -> list:
    """Filter file analyses to only include entities that are keys in the call graph"""
    # Only get entity IDs that are keys (callers) in the call graph, not values (callees)
    call_graph_keys = set(call_graph.keys())

    filtered_analyses = []
    for analysis in file_analyses:
        # Filter entities to only include those that are keys in the call graph
        filtered_entities = [entity for entity in analysis.entities if entity.id in call_graph_keys]

        if not filtered_entities:
            continue

        filtered_analysis = analysis.model_copy()
        filtered_analysis.entities = filtered_entities
        filtered_analyses.append(filtered_analysis)

    logger.info(f"Filtered file analyses from {len(file_analyses)} to {len(filtered_analyses)} files")
    return filtered_analyses


def _optimize_data_for_llm(data: dict, codebase_path: str) -> dict:
    """Optimize data for LLM by removing unnecessary keys and trimming IDs"""
    optimized = data.copy()
    optimized["call_graph"] = _optimize_call_graph(data["call_graph"])
    optimized["file_analyses"] = _optimize_file_analyses(data["file_analyses"], codebase_path)
    optimized["key_components"] = _optimize_key_components(data["key_components"], codebase_path)
    return optimized


def _optimize_call_graph(call_graph: dict) -> dict:
    """Remove stuff before ':' and empty calls"""
    optimized_call_graph = {}
    for entity_id, calls in call_graph.items():
        short_id = entity_id.split(":")[-1]
        short_calls = [call.split(":")[-1] for call in calls if call]

        if short_calls:
            optimized_call_graph[short_id] = short_calls

    return optimized_call_graph


def _optimize_file_analyses(file_analyses: list, codebase_path: str) -> list:
    """Optimize file analyses by keeping only essential entity data"""
    prefix = codebase_path + "/"
    optimized_analyses = []
    for analysis in file_analyses:
        optimized_entities = [_optimize_entity(entity) for entity in analysis["entities"]]
        optimized_entities = [entity for entity in optimized_entities if entity]

        if optimized_entities:
            # Trim codebase prefix from file path
            file_path = analysis["file_path"][len(prefix) :]
            optimized_analyses.append({"file_path": file_path, "entities": optimized_entities})

    return optimized_analyses


def _optimize_entity(entity: dict) -> dict:
    """Optimize a single entity by keeping only essential fields"""
    optimized_entity = {}

    # Always present fields
    optimized_entity["type"] = entity["type"]
    optimized_entity["signature"] = entity["signature"]

    # Optional fields
    if entity.get("parent"):
        optimized_entity["parent"] = entity["parent"]

    # Calls: keep only full_call as array of strings
    if entity.get("calls"):
        full_calls = [call["full_call"] for call in entity["calls"] if call.get("full_call")]
        if full_calls:
            optimized_entity["calls"] = full_calls

    # Called_by: remove stuff before ":"
    if entity.get("called_by"):
        short_called_by = [cb.split(":")[-1] for cb in entity["called_by"] if cb]
        if short_called_by:
            optimized_entity["called_by"] = short_called_by

    return optimized_entity


def _optimize_key_components(key_components: list, codebase_path: str) -> list:
    """Optimize key components by removing counts and trimming IDs"""
    prefix = codebase_path + "/"
    optimized_components = []
    for component in key_components:
        optimized_component = {
            "file": component["file"][len(prefix) :],
            "top_functions": [func["id"].split(":")[-1] for func in component.get("top_functions", [])],
        }
        optimized_components.append(optimized_component)

    return optimized_components
