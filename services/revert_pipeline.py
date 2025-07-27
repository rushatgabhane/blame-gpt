import logging
import os
import subprocess
from collections.abc import AsyncGenerator
from pathlib import Path

from libs.github import repo
from libs.helpers import is_production_environment
from services.docs_service.sync import CLONE_DIR, REPO_URL
from services.revert_service import revert_service

tracked_pull_requests = set()

logger = logging.getLogger(__name__)


async def run(pull_request_id: int) -> AsyncGenerator[str]:
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
        _cleanup(local_revert_branch, new_dir)
        _sync_repo(new_dir)
        yield "repo synced"

        logger.info(f"Checking out to branch {local_revert_branch}...")
        subprocess.run(["git", "-C", str(new_dir), "checkout", "-b", local_revert_branch])
        logger.info(f"checked out to branch {local_revert_branch}")
        commit_sha = pull_request.merge_commit_sha

        logger.info(f"Found commit {commit_sha} to revert. Reverting...")
        git_revert_status = subprocess.run(
            ["git", "-C", str(new_dir), "revert", "--no-edit", commit_sha, "-m", f"Revert PR {pull_request_id} by BlameGPT"],
            stderr=subprocess.STDOUT,
        )
        pr_body = f"PR to revert changes in #{pull_request_id}."

        if git_revert_status.returncode != 0:
            # 1. get file patches
            # by this time, the new branch is already created but the git revert commit has failed
            # 2. send patches (filename, edits) to the LLM - skipped for now
            # 3. get edit suggestions for each file - skipped for now
            # 4. apply edits - skipped for now
            # 5. commit
            # 6. push branch to remote
            # 7. open PR
            subprocess.run(["git", "-C", str(new_dir), "revert", "--abort"])
            logger.info("git revert failed, reverting with AI...")
            revert_service.revert_with_ai(pull_request)
            pr_body = f"{pr_body} \nWARNING: AI created this pull request, please verify the changes before merging"

        created_pull_request = None
        if not is_production_environment():
            logger.info("Opening PR with changes...")
            subprocess.run(["git", "-C", str(new_dir), "push", "origin", local_revert_branch], check=True)
            logger.info(f"Branch {local_revert_branch} pushed to remote.")
            created_pull_request = repo.create_pull(
                base=pull_request.base.ref,
                head=local_revert_branch,
                title=f"Revert PR #{pull_request_id}",
                body=pr_body,
                maintainer_can_modify=True,
            )
            logger.info(f"PR {created_pull_request.id} opened at {created_pull_request.html_url}")

        if created_pull_request:
            yield f"revert pipeline completed. PR {created_pull_request.id} opened at {created_pull_request.html_url}"
        else:
            yield "revert pipeline completed. Changes committed locally (non-production environment)"

    except Exception as e:
        logger.exception(f"{pull_request_id}: error in revert pipeline {e}")
        yield f"some error occurred in revert pipeline. please report this issue with the pull request id: {pull_request_id}"

    _cleanup(local_revert_branch, new_dir)
    tracked_pull_requests.remove(pull_request_id)


def _delete_new_branch(local_revert_branch: str, directory_path: Path):
    subprocess.run(
        ["git", "-C", str(directory_path), "checkout", "main"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    subprocess.run(
        ["git", "-C", str(directory_path), "branch", "-D", local_revert_branch],
        # check=True,
        stdout=subprocess.PIPE,
        text=True,
    )


def _sync_repo(dir: Path):
    os.mkdir(dir)
    subprocess.run(["git", "clone", REPO_URL, str(dir)], check=True, stderr=subprocess.PIPE, text=True)


def _cleanup(local_revert_branch: str, directory_path: Path):
    _delete_new_branch(local_revert_branch, directory_path)
    subprocess.run(["rm", "-rf", str(directory_path)])
