import logging
from libs.llm import llmReasoningCheap
from libs.prompt_templates.test_steps_generation import test_steps_generation_parser, test_steps_prompt
from models.models import PullRequest, TestStepsGeneration

logger = logging.getLogger(__name__)


def generate_test_steps(pull_request: PullRequest) -> TestStepsGeneration | None:
    """
    Generate test steps for a given pull request using an LLM.
    """
    if not pull_request.code_diff_summary or not pull_request.explaination:
        logger.warning(f"Pull request #{pull_request.id} does not have code diff summary or explanation.")
        return None

    prompt = test_steps_prompt(
        code_diff_summary=pull_request.code_diff_summary,
        explanation=pull_request.explaination,
        title=pull_request.title,
    )

    try:
        response = llmReasoningCheap.invoke(prompt)
        steps = test_steps_generation_parser.invoke(response)
        assert isinstance(steps, TestStepsGeneration, "Test steps generation parsing failed")

        return steps
    except Exception as e:
        logger.error(f"Error generating test steps for PR #{pull_request.id}: {e}")
        return None
