import logging
from libs.llm import llmReasoning
from libs.sqlite.core.core_sqlite_client import Database
from models.models import CodeDiffSummary, PullRequest
from services.github import pull_request_service, test_steps_generation_service, comment_service

logger = logging.getLogger(__name__)


async def run(pull_request_id: int, db: Database):
    try:
        yield f"starting pull request blame pipeline for PR #{pull_request_id}"

        # 1. get PR, need to add to DB and track whethere processed or not
        # if processed, skip else, process

        # db.add_pull_request fetches the PR from GitHub by calling _get_pr_with_embeddings
        pull_request: PullRequest = db.add_pull_request(pull_request_id)

        # now that we have the PR, the diff summary and the explanation
        # let's feed it to the LLM to get the steps to test the PR
        test_steps = test_steps_generation_service.generate_test_steps(pull_request)
        if not test_steps:
            yield f"no test steps generated for PR #{pull_request_id}"
            logger.warning(f"PR #{pull_request_id}: no test steps generated")
            return
        yield f"test steps generated for PR #{pull_request_id}"

        # add comment to PR with the test steps
        comment = f"## Steps to test the PR: \n" + test_steps.steps + "\n\n ### Powered by BlameGPT"

        comment_service.add_comment_to_pull_request(pull_request_id, comment)
        yield "added comment to the PR."

        # TODO: update in the DB that the test steps were generated for this PR
        yield f"Test steps added successfully for PR #{pull_request_id}!"

    except Exception as e:
        string = f"Error in test_steps pipeline for pull_request_id: {pull_request_id}"
        logger.error(string)
        yield string
