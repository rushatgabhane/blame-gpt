import logging
import subprocess
from collections.abc import AsyncGenerator

from libs.github import repo
from libs.helpers import is_production_environment
from libs.sqlite.docs.docs_sqlite_client import Database
from services.docs_service.sync import CLONE_DIR, sync_docs
from services.revert_service import revert_service

logger = logging.getLogger(__name__)


async def run(pull_request_id: int, db: Database) -> AsyncGenerator[str]:
    # 1. problematic PR is always closed, so get the merge commit SHA from the PR
    # 2. git checkout -b revert-{pr_id}
    # 3. git revert the commit from 1
    # 4. can't track if a PR is processed because the files can't be saved on disk

    try:
        yield "starting the revert pipeline, syncing repo"
        pull_request = repo.get_pull(pull_request_id)
        pull_request_id = pull_request.number
        local_revert_branch = f"revert-{pull_request.number}"
        logger.info("Syncing repo...")
        sync_docs(db)
        yield "repo synced"
        logger.info(f"Checking out to branch {local_revert_branch}...")
        # delete if exists
        _delete_new_branch(local_revert_branch)
        subprocess.run(["git", "-C", str(CLONE_DIR), "checkout", "-b", local_revert_branch])
        yield f"checked out to branch {local_revert_branch}"

        if pull_request.merged:
            commit_sha = pull_request.merge_commit_sha

            logger.info("Comparing staging branch with production to find commits...")
            logger.info("Iterating through commits...")

            logger.info(f"Found commit {commit_sha} to revert. Reverting...")
            git_revert_status = subprocess.run(
                ["git", "-C", str(CLONE_DIR), "revert", "--no-edit", commit_sha, "-m", "1"],
                stderr=subprocess.STDOUT,
            )

            if git_revert_status != 0:
                # 1. get file patches
                # by this time, the new branch is already created but the git revert commit has failed
                # 2. send patches (filename, edits) to the LLM
                # 3. get edit suggestions for each file
                # 4. apply edits
                # 5. commit
                # 6. open PR
                subprocess.run(["git", "-C", str(CLONE_DIR), "revert", "--abort"])
                logger.info("git revert failed, reverting with AI...")
                revert_service.revert_with_ai(pull_request)

            created_pull_request = None
            if is_production_environment():
                logger.info("Opening PR with changes...")
                subprocess.run(["git", "-C", str(CLONE_DIR), "push", "origin", local_revert_branch], check=True)
                created_pull_request = repo.create_pull(
                    base=pull_request.base.ref,
                    head=local_revert_branch,
                    title=f"Revert PR #{pull_request_id}",
                    body=f"PR to revert changes in #{pull_request_id}",
                    maintainer_can_modify=True,
                )
                logger.info(f"PR {created_pull_request.id} opened at {created_pull_request.html_url}")

            _delete_new_branch(local_revert_branch)
            if created_pull_request:
                yield f"revert pipeline completed. PR {created_pull_request.id} opened at {created_pull_request.html_url}"
            else:
                yield "revert pipeline completed. Changes committed locally (non-production environment"
        else:
            yield "PR is not merged. Skipping..."
            return
    except Exception as e:
        logger.exception(f"{pull_request_id}: error in revert pipeline {e}")
        _delete_new_branch(local_revert_branch)
        yield f"some error occurred in revert pipeline. please report this issue with the pull request id: {pull_request_id}"


def _delete_new_branch(local_revert_branch: str):
    subprocess.run(
        ["git", "-C", str(CLONE_DIR), "checkout", "main"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    subprocess.run(
        ["git", "-C", str(CLONE_DIR), "branch", "-D", local_revert_branch],
        stdout=subprocess.PIPE,
        text=True,
    )
