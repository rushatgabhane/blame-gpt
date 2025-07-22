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
    # 1. problematic PR is always closed, so look for the commit r"Merge pull request #(\d+)"
    # 2. git checkout -b revert-{pr_id}
    # 3. git revert the commit from 1
    # 4. can't track if a PR is processed because the files can't be saved on disk

    try:
        yield "starting the revert pipeline, syncing repo"
        local_revert_branch = f"revert-{pull_request_id}"
        logger.info("Syncing repo...")
        sync_docs(db)
        yield "repo synced"
        logger.info(f"Checking out to branch {local_revert_branch}...")
        # delete if exists
        _delete_new_branch(local_revert_branch)
        subprocess.run(
            ["git", "-C", str(CLONE_DIR), "checkout", "-b", local_revert_branch],
            # check=True,
            # stdout=subprocess.DEVNULL,
            # stderr=subprocess.DEVNULL,
        )
        yield f"checked out to branch {local_revert_branch}"

        logger.info("Comparing staging branch with production to find commits...")
        comparison = repo.compare("production", "staging")
        logger.info("Iterating through commits...")
        for commit in comparison.commits:
            if commit.commit.message.startswith(f"Merge pull request #{pull_request_id}"):
                logger.info(f"Found commit {commit.sha} to revert. Reverting...")
                git_revert_status = subprocess.run(
                    ["git", "-C", str(CLONE_DIR), "revert", "--no-edit", commit.sha, "-m", "1"],
                    stderr=subprocess.STDOUT,
                )

                if git_revert_status.returncode >= 0:
                    # 1. get file patches
                    # by this time, the new is already created but the git revert commit has failed
                    # 2. send patches (filename, edits) to the LLM
                    # 3. get edit suggestions for each file
                    # 4. apply edits
                    # 5. commit
                    # 6. open PR
                    subprocess.run(["git", "-C", str(CLONE_DIR), "revert", "--abort"])
                    logger.info("git revert failed, reverting with AI...")
                    revert_service.revert_with_ai(repo, pull_request_id, commit)

                break

        pull_request = None
        if is_production_environment():
            logger.info("Opening PR with changes...")
            pull_request = repo.create_pull(
                base="staging",  # confirm if correct base?
                head=local_revert_branch,
                title=f"Revert PR #{pull_request_id}",  # probably need a better title and body
                body=f"PR to revert changes in #{pull_request_id}",
                maintainer_can_modify=True,
            )
            logger.info(f"PR {pull_request.id} opened at {pull_request.url}")

        _delete_new_branch(local_revert_branch)
        if pull_request:
            yield f"revert pipeline completed. PR {pull_request.id} opened at {pull_request.url}"
        else:
            yield "revert pipeline completed. Changes committed locally (non-production environment"

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
        # check=True,
        stdout=subprocess.PIPE,
        text=True,
    )
