import logging
import subprocess
from collections.abc import AsyncGenerator

from libs.github import repo
from libs.sqlite.docs.docs_sqlite_client import Database
from services.docs_service.sync import CLONE_DIR, sync_docs

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
        subprocess.run(
            ["git", "-C", str(CLONE_DIR), "checkout", "main"],
            # check=True,
            # stdout=subprocess.DEVNULL,
            # stderr=subprocess.DEVNULL,
        )
        subprocess.run(
            ["git", "-C", str(CLONE_DIR), "branch", "-D", local_revert_branch],
            # check=True,
            stdout=subprocess.PIPE,
            text=True,
            # stderr=subprocess.DEVNULL,
        )
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
                subprocess.run(
                    ["git", "-C", str(CLONE_DIR), "revert", commit.sha, "-m", "1"],
                    check=True,
                    # stdout=subprocess.STDOUT,
                    stderr=subprocess.STDOUT,
                )
                logger.info("Committing changes...")
                subprocess.run(["git", "-C", str(CLONE_DIR), "commit", "-am", f"Revert #{pull_request_id}"], check=True)
                logger.info("Changes committed")
                break

        yield "revert pipeline completed"

    except Exception as e:
        logger.exception(f"{pull_request_id}: error in revert pipeline {e}")
        yield f"some error occurred in revert pipeline. please report this issue with the pull request id: {pull_request_id}"
