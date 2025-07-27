import logging
import os
import subprocess
from collections.abc import AsyncGenerator
from pathlib import Path

from libs.github import repo
from libs.helpers import is_production_environment
from libs.sqlite.docs.docs_sqlite_client import Database
from services.docs_service.sync import CLONE_DIR, sync_docs

tracked_pull_requests = set()

logger = logging.getLogger(__name__)


async def run(pull_request_id: int, db: Database) -> AsyncGenerator[str]:
    # 1. problematic PR is always closed, so get the merge commit SHA from the PR
    # 2. git checkout -b revert-{pr_id}
    # 3. git revert the commit from 1
    # 4. can't track if a PR is processed because the files can't be saved on disk

    if pull_request_id in tracked_pull_requests:
        yield "Revert PR request already received."
        return

    # lock PR
    tracked_pull_requests.add(pull_request_id)
    new_dir = Path.joinpath(CLONE_DIR, f"../revert-{pull_request_id}")
    try:
        yield "starting the revert pipeline, syncing repo"
        pull_request = repo.get_pull(pull_request_id)

        if not pull_request.merged:
            yield "PR is not merged. Skipping..."
            return

        pull_request_id = pull_request.number
        local_revert_branch = f"revert-{pull_request.number}"
        logger.info("Syncing repo...")
        # delete if exists
        _cleanup(new_dir)
        _sync_repo(new_dir, db)
        yield "repo synced"

        logger.info(f"Checking out to branch {local_revert_branch}...")
        subprocess.run(["git", "-C", str(new_dir), "checkout", "-b", local_revert_branch])
        yield f"checked out to branch {local_revert_branch}"
        commit_sha = pull_request.merge_commit_sha

        logger.info(f"Found commit {commit_sha} to revert. Reverting...")
        git_revert_status = subprocess.run(
            ["git", "-C", str(new_dir), "revert", "--no-edit", commit_sha, "-m", "1"],
            stderr=subprocess.STDOUT,
        )

        if git_revert_status.returncode != 0:
            subprocess.run(["git", "-C", str(new_dir), "revert", "--abort"])
            logger.info("git revert failed, returning...")
            _cleanup(new_dir)
            tracked_pull_requests.remove(pull_request_id)
            yield "Could not revert PR, skipping..."
            return

        created_pull_request = None
        if is_production_environment():
            logger.info("Opening PR with changes...")
            subprocess.run(["git", "-C", str(new_dir), "push", "origin", local_revert_branch], check=True)
            logger.info(f"Branch {local_revert_branch} pushed to remote.")
            created_pull_request = repo.create_pull(
                base=pull_request.base.ref,
                head=local_revert_branch,
                title=f"Revert PR #{pull_request_id}",
                body=f"PR to revert changes in #{pull_request_id}",
                maintainer_can_modify=True,
            )
            logger.info(f"PR {created_pull_request.id} opened at {created_pull_request.html_url}")

        if created_pull_request:
            yield f"revert pipeline completed. PR {created_pull_request.id} opened at {created_pull_request.html_url}"
        else:
            yield "revert pipeline completed. Changes committed locally (non-production environment"

    except Exception as e:
        logger.exception(f"{pull_request_id}: error in revert pipeline {e}")
        yield f"some error occurred in revert pipeline. please report this issue with the pull request id: {pull_request_id}"

    _cleanup(new_dir)
    tracked_pull_requests.remove(pull_request_id)


def _sync_repo(dir: Path, db: Database):
    # cannot do a shallow clone because then the normal git revert will happen incorrectly.
    # for example, since it shallow clones, it won't have any previous commits so when
    # reverting, it will actually delete all the files in the commit

    sync_docs(db)
    os.mkdir(dir)
    subprocess.run(["cp", "-r", str(CLONE_DIR) +'/.', str(dir)], check=True, stderr=subprocess.PIPE, text=True)


def _cleanup(directory_path: Path):
    # since the folder itslef is being deleted, there is no
    # need to delete the branch separately
    subprocess.run(["rm", "-rf", str(directory_path)])
