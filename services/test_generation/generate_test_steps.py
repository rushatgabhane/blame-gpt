import asyncio
import logging
import random

from libs.helpers import cosine_similarity
from libs.llm import ModelNames, llm
from libs.prompt_templates.consolidate_test_steps import consolidate_test_steps_parser, consolidate_test_steps_prompt
from libs.prompt_templates.issue_test_steps_for_bug import issue_steps_for_bug_parser, issue_steps_for_bug_prompt
from libs.prompt_templates.pull_request_test_steps import test_steps_generation_parser, test_steps_prompt
from libs.sqlite.core.core_sqlite_client import Database
from models.models import GeneratedTestSteps, GeneratedTestStepsList, Issue, PullRequest, TestSuite
from services.github import comment_service, issue_service, pull_request_service
from services.user_service import track_llm_usage

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


async def generate_test_steps_for_pull_request(
    pull_request_id: int, db: Database, usage_log_id: int | None = None
) -> GeneratedTestStepsList | None:
    """
    Asynchronously generates, consolidates, and posts AI-generated test steps for a given GitHub pull request.
    
    If test steps have already been generated for the pull request, the function skips processing. Otherwise, it fetches the pull request and its linked issues, retrieves or generates test steps for those issues, and finds similar existing test suites. It then uses a large language model to generate new test steps for the pull request, consolidates them if necessary to remove redundancy, formats the result as a comment, posts it to the pull request, and stores the comment in the database.
    
    Returns:
        GeneratedTestStepsList: The generated and consolidated test steps, or None if generation fails at any stage.
    """
    if db.has_generated_test_steps(pull_request_id):
        logger.info(f"PR #{pull_request_id}: test steps already generated, skipping.")
        return None

    pull_request = pull_request_service.add_pull_request_if_not_exist(pull_request_id, db, usage_log_id)
    if not pull_request:
        logger.error(f"PR #{pull_request_id}: failed to fetch.")
        return None

    if not pull_request.linked_issue_ids:
        logger.error(f"PR #{pull_request_id}: no linked issue ids found.")
        return None

    linked_issue_test_steps = await _get_test_steps_from_linked_issues(pull_request.linked_issue_ids, db, usage_log_id)
    logger.info(f"PR #{pull_request_id}: fetched linked issue tests {len(linked_issue_test_steps or [])}")

    similar_existing_steps = _find_similar_test_steps(pull_request.embedding or [], db)

    test_steps = await _generate_test_steps(
        pull_request, linked_issue_test_steps, similar_existing_steps, db, usage_log_id
    )
    if not test_steps or not test_steps.test or test_steps.test == []:
        logger.error(f"PR #{pull_request_id}: failed to generate test steps.")
        return None

    # Consolidate similar test steps to remove repetitive details
    if len(test_steps.test) > 1:
        consolidated_steps = await _consolidate_test_steps(test_steps, db, usage_log_id)
        if consolidated_steps:
            test_steps = consolidated_steps

    comment = _format_comment(test_steps=test_steps)
    comment_service.add_comment_to_pull_request(pull_request_id, comment)

    db.add_pull_request_test_steps(pull_request_id, comment)

    logger.info(f"PR #{pull_request_id}: generated test steps successfully.")
    return test_steps


# Experiment with issue embedding for similar.
def _find_similar_test_steps(pr_embedding: list[float], db: Database) -> list[TestSuite]:
    if not pr_embedding:
        logger.warning("no PR embedding provided for finding similar test steps.")
        return []
    existing_steps = db.get_all_test_suites()
    k = 5
    similar_steps = sorted(existing_steps, key=lambda x: cosine_similarity(x.embedding, pr_embedding), reverse=True)[:k]
    return similar_steps


async def _get_test_steps_from_linked_issues(
    linked_issue_ids: list[int], db: Database, usage_log_id: int | None = None
) -> list[GeneratedTestSteps] | None:
    issue_tasks = [issue_service.add_issue_if_not_exists(issue_id, db=db) for issue_id in linked_issue_ids]
    issues = await asyncio.gather(*issue_tasks)
    linked_issues = [issue for issue in issues if issue]

    tasks = [_generate_test_step_for_issue(issue, db, usage_log_id) for issue in linked_issues]
    results = await asyncio.gather(*tasks)
    tests_for_all_linked_issues = [r for r in results if r]
    return tests_for_all_linked_issues


async def _generate_test_step_for_issue(
    issue: Issue, db: Database, usage_log_id: int | None = None
) -> GeneratedTestSteps | None:
    body = issue.steps if issue.steps != "" else issue.raw_body
    prompt = issue_steps_for_bug_prompt.format(
        title=issue.title,
        body=body,
    )

    try:
        response = llm.invoke(prompt)
        track_llm_usage(db, usage_log_id, response, ModelNames.GPT_4_1)
        generated_steps = issue_steps_for_bug_parser.invoke(response)
        assert isinstance(generated_steps, GeneratedTestSteps)
        return generated_steps

    except Exception as e:
        logger.error(f"error generating test steps for issue #{issue.id}: {e}")
        return None


async def _generate_test_steps(
    pull_request: PullRequest,
    linked_issue_test_steps: list[GeneratedTestSteps] | None,
    similar_test_steps: list[TestSuite],
    db: Database,
    usage_log_id: int | None = None,
) -> GeneratedTestStepsList | None:
    if not pull_request.code_diff_summary:
        return None

    linked_issue_test_steps_str = "\n\n".join(
        f"### {t.title}\n"
        + (f"Precondition: {t.precondition}\n" if t.precondition else "")
        + "\n".join(line for line in t.steps.splitlines() if line.strip())
        for t in linked_issue_test_steps or []
    )

    similar_test_steps_str = "\n\n".join(
        f"### {s.title}\n" + "\n".join(line for line in s.steps.splitlines() if line.strip())
        for s in similar_test_steps or []
    )

    prompt = test_steps_prompt.format(
        linked_issue_test_steps=linked_issue_test_steps_str,
        similar_test_steps=similar_test_steps_str,
        title=pull_request.title,
        diff_summary=pull_request.code_diff_summary,
    )

    try:
        response = llm.invoke(prompt)
        track_llm_usage(db, usage_log_id, response, ModelNames.GPT_4_1)
        steps = test_steps_generation_parser.invoke(response)
        assert isinstance(steps, GeneratedTestStepsList)

        return steps
    except Exception as e:
        logger.error(f"Error generating test steps for PR #{pull_request.id}: {e}")
        return None


async def _consolidate_test_steps(
    test_steps: GeneratedTestStepsList, db: Database, usage_log_id: int | None = None
) -> GeneratedTestStepsList | None:
    """Consolidate similar test steps to remove repetitive details."""
    try:
        # Format the original test steps for the consolidation prompt
        original_test_steps_str = "\n\n".join(
            f"Test {i + 1}: {t.title}\n"
            + (f"Precondition: {t.precondition}\n" if t.precondition else "")
            + "\n".join(line for line in t.steps.splitlines() if line.strip())
            for i, t in enumerate(test_steps.test)
        )

        prompt = consolidate_test_steps_prompt.format(original_test_steps=original_test_steps_str)

        response = llm.invoke(prompt)
        track_llm_usage(db, usage_log_id, response, ModelNames.GPT_4_1)
        consolidated_steps = consolidate_test_steps_parser.invoke(response)
        assert isinstance(consolidated_steps, GeneratedTestStepsList)

        return consolidated_steps

    except Exception as e:
        logger.error(f"Error consolidating test steps: {e}")
        return None


def _format_comment(test_steps: GeneratedTestStepsList) -> str:
    random.seed()
    comment_title = random.choice(_sassy_titles)
    sections = []
    for t in test_steps.test:
        section = ""
        if t.precondition:
            section += f"Precondition: {t.precondition}\n"
        section += f"### {t.title}\n"
        section += "\n".join(line for line in t.steps.splitlines() if line.strip())
        sections.append(section)

    all_tests = "\n\n".join(sections)

    return f"""
### {comment_title}
```markdown
{all_tests}
```
<sub>AI generated these steps. Your quick sanity check makes them solid.</sub>
"""
