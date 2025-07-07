import logging

from libs.sqlite.core.core_sqlite_client import Database
from models.models import PullRequest
from services.github import comment_service, pull_request_service
from services.test_steps import test_steps_generation_service

logger = logging.getLogger(__name__)


async def run(pull_request_id: int, db: Database):
    try:
        yield f"starting pull request blame pipeline for PR #{pull_request_id}"

        # 1. get PR, need to add to DB and track whether processed or not
        # if processed, skip else, process
        pr = db.get_pull_request_test_steps(pull_request_id)

        if pr and pr.test_steps:
            yield f"test steps already generated for PR #{pull_request_id}. skipping."
            logger.info(f"PR #{pull_request_id}: test steps already generated. skipping.")
            return

        # db.add_pull_request fetches the PR from GitHub by calling _get_pr_with_embeddings
        pull_request: PullRequest = pull_request_service.add_pull_request(pull_request_id)

        # now that we have the PR, the diff summary and the explanation
        # let's feed it to the LLM to get the steps to test the PR
        test_steps = test_steps_generation_service.generate_test_steps(pull_request)
        if not test_steps:
            yield f"no test steps generated for PR #{pull_request_id}"
            logger.warning(f"PR #{pull_request_id}: no test steps generated")
            return
        yield f"test steps generated for PR #{pull_request_id}"

        # add comment to PR with the test steps
        comment = f"""
### Suggested steps
{test_steps.steps}
        
<sub>AI generated these steps. Your quick sanity check makes them solid.</sub>

        comment_service.add_comment_to_pull_request(pull_request_id, comment)
        yield "added comment to the PR."

        # update in the DB that the test steps were generated for this PR
        db.update_pull_request_test_steps(pull_request_id, test_steps.steps)
        yield f"Test steps added successfully for PR #{pull_request_id}!"

    except Exception as e:
        string = f"Error in test_steps pipeline for pull_request_id {pull_request_id}, error: {str(e)}"
        logger.error(string)
        yield string
