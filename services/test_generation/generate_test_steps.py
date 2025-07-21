import logging
import random

from libs import constants
from libs.llm import llm
from libs.prompt_templates.consolidate_test_steps import consolidate_test_steps_parser, consolidate_test_steps_prompt
from libs.prompt_templates.issue_test_steps_for_bug import issue_steps_for_bug_parser, issue_steps_for_bug_prompt
from libs.prompt_templates.pull_request_test_steps import test_steps_generation_parser, test_steps_prompt
from libs.sqlite.core.core_sqlite_client import Database
from models.models import GeneratedTestStepsList, PullRequest, TestSuite
from services.github import comment_service

logger = logging.getLogger(__name__)

_sassy_titles = [
    "Ready for your test drive 🏎️",
    "Time to break it (gently)",
    "Checklist for the brave",
    "Let's see if it holds up!",
    "Reviewers, do your thing!",
    "Test steps, fresh out the oven",
    "Give it a whirl!",
]


async def generate_test_steps_for_pull_request(pull_request_id: int, db: Database) -> GeneratedTestStepsList | None:
    """
    Generate test steps for a pull request by analyzing similar existing test cases.

    This function now uses vector search for efficient similarity matching,
    replacing the previous memory-intensive caching approach.
    """
    if db.has_generated_test_steps(pull_request_id):
        logger.info(f"test steps already generated for pull request {pull_request_id}")
        return None

    logger.info(f"generating test steps for pull request {pull_request_id}")

    # Get PR with embedding
    pr = db.get_pull_request_by_id_with_embedding(pull_request_id)
    if not pr:
        logger.info(f"pull request {pull_request_id} not found")
        return None

    if not pr.embedding:
        logger.info(f"no embedding found for pull request {pull_request_id}")
        return None

    # Find similar test steps using vector search (replaces memory cache)
    similar_steps = _find_similar_test_steps(pr.embedding, db)

    if not similar_steps:
        logger.info(f"no similar test steps found for pull request {pull_request_id}")
        return None

    logger.info(f"found {len(similar_steps)} similar test steps for pull request {pull_request_id}")

    # Get additional context from linked issues
    linked_issues_test_steps = await _get_test_steps_from_linked_issues(pr, db)

    # Generate test steps using LLM
    test_steps_prompt_filled = test_steps_prompt.format(
        pr_title=pr.title,
        pr_summary=pr.explaination or "No summary provided",
        similar_test_steps="\n".join([f"- {step.title}: {step.steps}" for step in similar_steps]),
        linked_issues_test_steps=linked_issues_test_steps,
    )

    response = await llm.ainvoke(test_steps_prompt_filled)
    parsed_response = test_steps_generation_parser.invoke(response)

    test_steps_list = GeneratedTestStepsList(test_steps=parsed_response.test_steps)

    # Store the generated test steps
    db.add_pull_request_test_steps(pull_request_id, test_steps_list.model_dump_json())

    return test_steps_list


def _find_similar_test_steps(pr_embedding: list[float], db: Database) -> list[TestSuite]:
    """
    Find similar test steps using vector search.
    Args:
        pr_embedding: The embedding vector of the pull request
        db: Database instance with vector search capabilities

    Returns:
        List of similar TestSuite objects, sorted by similarity
    """
    if not pr_embedding:
        logger.info("no PR embedding provided for finding similar test steps.")
        return []

    try:
        similar_steps = db.find_similar_test_suites(pr_embedding, k=constants.VECTOR_SEARCH_K)

        if similar_steps:
            logger.info(f"Found {len(similar_steps)} similar test steps using vector search")
        else:
            logger.info("No similar test steps found")

        return similar_steps

    except Exception as e:
        logger.error(f"Error finding similar test steps: {e}", exc_info=True)
        return []


async def _get_test_steps_from_linked_issues(pr: PullRequest, db: Database) -> str:
    """Get test steps from issues linked to the pull request"""
    if not pr.linked_issue_ids:
        return "No linked issues found."

    linked_test_steps = []
    for issue_id in pr.linked_issue_ids:
        issue = db.get_issue_by_id(issue_id)
        if issue and issue.steps:
            linked_test_steps.append(f"Issue #{issue_id}: {issue.steps}")

    if not linked_test_steps:
        return "No test steps found in linked issues."

    return "\n".join(linked_test_steps)


async def generate_test_steps_from_issue(issue_id: int, db: Database) -> str | None:
    """Generate test steps for a bug issue"""
    logger.info(f"generating test steps for issue {issue_id}")

    try:
        issue = db.get_issue_by_id(issue_id)
        if not issue:
            logger.info(f"issue {issue_id} not found")
            return None

        # Use vector search to find similar test steps for the issue
        if issue.embedding:
            similar_steps = _find_similar_test_steps(issue.embedding, db)
            similar_steps_text = "\n".join([f"- {step.title}: {step.steps}" for step in similar_steps])
        else:
            similar_steps_text = "No similar test steps found."

        test_steps_prompt_filled = issue_steps_for_bug_prompt.format(
            issue_title=issue.title,
            issue_body=issue.raw_body or "No description provided",
            similar_test_steps=similar_steps_text,
        )

        response = await llm.ainvoke(test_steps_prompt_filled)
        parsed_response = issue_steps_for_bug_parser.invoke(response)

        return parsed_response.test_steps

    except Exception as e:
        logger.error(f"Error generating test steps for issue {issue_id}: {e}", exc_info=True)
        return None


async def consolidate_test_steps_for_pull_request(pull_request_id: int, db: Database) -> str | None:
    """Consolidate and improve existing test steps for a pull request"""
    logger.info(f"consolidating test steps for pull request {pull_request_id}")

    # Get existing test steps
    existing_steps = db.get_pull_request_test_steps(pull_request_id)
    if not existing_steps:
        logger.info(f"no existing test steps found for pull request {pull_request_id}")
        return None

    # Get PR details
    pr = db.get_pull_request_by_id_with_embedding(pull_request_id)
    if not pr:
        logger.info(f"pull request {pull_request_id} not found")
        return None

    # Find similar test steps for additional context
    similar_steps = []
    if pr.embedding:
        similar_steps = _find_similar_test_steps(pr.embedding, db)

    similar_steps_text = "\n".join([f"- {step.title}: {step.steps}" for step in similar_steps])

    consolidation_prompt_filled = consolidate_test_steps_prompt.format(
        pr_title=pr.title,
        pr_summary=pr.explaination or "No summary provided",
        existing_test_steps=existing_steps,
        similar_test_steps=similar_steps_text,
    )

    response = await llm.ainvoke(consolidation_prompt_filled)
    parsed_response = consolidate_test_steps_parser.invoke(response)

    # Update the stored test steps
    db.add_pull_request_test_steps(pull_request_id, parsed_response.consolidated_test_steps)

    return parsed_response.consolidated_test_steps


async def post_test_steps_to_github(
    pull_request_id: int, test_steps: GeneratedTestStepsList | str, db: Database
) -> bool:
    """Post generated test steps as a comment on the GitHub pull request"""
    try:
        # Format test steps for GitHub comment
        if isinstance(test_steps, GeneratedTestStepsList):
            steps_text = "\n".join([f"{i + 1}. {step.step}" for i, step in enumerate(test_steps.test_steps)])
        else:
            steps_text = test_steps

        # Choose a random sassy title
        title = random.choice(_sassy_titles)

        comment_body = f"## {title}\n\n{steps_text}"

        # Post comment using the GitHub service
        success = await comment_service.post_comment_to_pull_request(pull_request_id, comment_body)

        if success:
            logger.info(f"Successfully posted test steps comment to PR #{pull_request_id}")
        else:
            logger.error(f"Failed to post test steps comment to PR #{pull_request_id}")

        return success

    except Exception as e:
        logger.error(f"Error posting test steps to GitHub for PR #{pull_request_id}: {e}")
        return False
