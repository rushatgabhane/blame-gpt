import contextlib
import fcntl
import logging
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import pathspec

from libs.bitbucket import get_access_token

logger = logging.getLogger(__name__)


class LocalRepository:
    """
    Context manager for local Bitbucket repository operations with automatic cleanup.

    Bitbucket has no pull request refs (unlike GitHub's pull/N/head), so the source
    branch is fetched directly from the source repository (fork-safe).

    Usage:
        with LocalRepository(pull_request) as local_repo:
            if local_repo is None:
                return
            # Use local_repo.worktree_path for file operations
        # Automatic cleanup after out of scope
    """

    def __init__(self, pull_request: dict):
        self.pull_request = pull_request
        self.clone_path: str | None = None
        self.worktree_path: str | None = None
        self.branch_name: str | None = None
        self.fetch_url: str | None = None
        self.git_config_dir = tempfile.TemporaryDirectory(prefix="gitcfg-")
        self.askpass_script_path = self._create_askpass_script()

    def __enter__(self):
        try:
            pull_request_id = self.pull_request["id"]
            base_full_name = self.pull_request["destination"]["repository"]["full_name"]
            source_full_name = self.pull_request["source"]["repository"]["full_name"]
            source_branch = self.pull_request["source"]["branch"]["name"]

            clone_url = f"https://bitbucket.org/{base_full_name}.git"
            fetch_url = f"https://bitbucket.org/{source_full_name}.git"
            self.fetch_url = fetch_url

            sanitized_branch = source_branch.replace("/", "-")
            local_branch_name = f"pr-{pull_request_id}-{sanitized_branch}"

            base_name = f"blamegpt-{base_full_name}"
            worktree_name = f"blamegpt-{pull_request_id}-{sanitized_branch}"

            self.clone_path = self._safe_temp_path(base_name)
            self.worktree_path = self._safe_temp_path(worktree_name)
            self.branch_name = local_branch_name

            if not self.clone_path or not self.worktree_path:
                return None

            self._cleanup()
            self._create_or_update_clone(clone_url, fetch_url, source_branch, local_branch_name)
            self._create_worktree(local_branch_name)
            return self
        except Exception as e:
            logger.error(f"Failed to setup branch clone: {e}")
            self._cleanup()
            raise

    def _git_env(self):
        """
        Create an isolated git environment for secure credential handling.

        This prevents git operations from affecting global configuration and ensures
        credentials are stored only in the request-scoped temporary directory.

        Returns:
            dict: Environment variables that isolate git operations
        """
        env = os.environ.copy()
        env["GIT_CONFIG_GLOBAL"] = os.devnull  # disable global config
        env["GIT_CONFIG_SYSTEM"] = os.devnull  # disable system config
        env["GIT_CREDENTIAL_HELPER"] = ""  # disable all credential helpers
        env["HOME"] = str(Path(self.git_config_dir.name))  # isolated HOME
        env["GIT_TERMINAL_PROMPT"] = "0"  # disable interactive prompts
        env["GIT_ASKPASS"] = self.askpass_script_path
        env["SSH_AUTH_SOCK"] = ""  # disable SSH agent
        env["DISPLAY"] = ""  # disable GUI prompts
        return env

    def _create_askpass_script(self) -> str:
        token = get_access_token()
        askpass_script = f"""#!/bin/bash
if [[ "$1" == *"Username"* ]]; then
    echo "x-token-auth"
else
    echo "{token}"
fi
"""
        askpass_path = Path(self.git_config_dir.name) / "git-askpass.sh"
        with open(askpass_path, "w") as f:
            f.write(askpass_script)
        askpass_path.chmod(0o700)

        return str(askpass_path)

    def _create_or_update_clone(self, clone_url: str, fetch_url: str, source_branch: str, branch_name: str):
        if not self.clone_path:
            raise ValueError("Clone path not initialized")

        lock_file_path = f"{self.clone_path}.lock"
        env = self._git_env()

        with open(lock_file_path, "w") as lock_file:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            if not os.path.exists(self.clone_path):
                shallow_clone_cmd = ["git", "clone", "--no-checkout", "--depth", "1", clone_url, self.clone_path]
                subprocess.run(shallow_clone_cmd, check=True, capture_output=True, env=env)
                logger.info(f"Created shallow clone at {self.clone_path}")

            refspec = f"{source_branch}:refs/heads/{branch_name}"
            fetch_pr_branch_cmd = ["git", "fetch", fetch_url, refspec, "--force", "--no-tags", "--depth", "1"]
            result = subprocess.run(fetch_pr_branch_cmd, cwd=self.clone_path, capture_output=True, env=env)

            if result.returncode != 0:
                stderr_output = result.stderr.decode() if result.stderr else "No stderr"
                logger.error(f"Git fetch failed: {stderr_output}")
                raise subprocess.CalledProcessError(
                    result.returncode, fetch_pr_branch_cmd, result.stdout, result.stderr
                )

        with contextlib.suppress(OSError):
            os.unlink(lock_file_path)

    def _create_worktree(self, branch_name: str):
        if not self.clone_path or not self.worktree_path:
            raise ValueError("Paths not initialized")

        subprocess.run(
            ["git", "worktree", "add", self.worktree_path, branch_name],
            cwd=self.clone_path,
            check=True,
            capture_output=True,
            env=self._git_env(),
        )

    def _sanitize_path_component(self, name: str) -> str | None:
        """Sanitize and validate path components for security"""
        sanitized = re.sub(r"[^a-zA-Z0-9\-_.]", "-", name)

        if not sanitized or sanitized.isspace():
            return None

        if ".." in sanitized or sanitized.startswith("."):
            sanitized = sanitized.replace("..", "-").lstrip(".")

        return sanitized[:100]

    def _safe_temp_path(self, base_name: str) -> str | None:
        """Create a safe path within temp directory with validation"""
        temp_dir = tempfile.gettempdir()
        safe_base = self._sanitize_path_component(base_name)

        if safe_base is None:
            return None

        full_path = os.path.join(temp_dir, safe_base)

        # Verify path is actually within temp directory
        temp_dir_real = os.path.realpath(temp_dir)
        full_path_real = os.path.realpath(full_path)

        if not full_path_real.startswith(temp_dir_real + os.sep):
            return None

        return full_path

    def _cleanup(self):
        if not self.worktree_path or not self.clone_path:
            return

        if os.path.exists(self.clone_path) and os.path.exists(self.worktree_path):
            result = subprocess.run(
                ["git", "worktree", "remove", self.worktree_path, "--force"],
                cwd=self.clone_path,
                capture_output=True,
                env=self._git_env(),
            )
            if result.returncode != 0 and os.path.exists(self.worktree_path):
                shutil.rmtree(self.worktree_path)

        if self.branch_name and os.path.exists(self.clone_path):
            subprocess.run(
                ["git", "branch", "-D", self.branch_name],
                cwd=self.clone_path,
                capture_output=True,
                env=self._git_env(),
            )

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._cleanup()
        with contextlib.suppress(Exception):
            self.git_config_dir.cleanup()

    def head_sha(self) -> str | None:
        """Full commit sha of the PR head (the Bitbucket API only returns truncated hashes)."""
        if not self.worktree_path:
            return None

        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=self.worktree_path,
            capture_output=True,
            text=True,
            env=self._git_env(),
        )
        if result.returncode != 0:
            return None
        return result.stdout.strip()

    def get_incremental_diff(self, since_sha: str) -> str | None:
        """Diff of the PR head against a previously reviewed commit, fetched shallowly.

        Returns None when the commit can no longer be fetched (e.g. after a force push)
        so callers can fall back to a full review.
        """
        if not self.worktree_path or not self.fetch_url:
            return None

        env = self._git_env()
        fetch = subprocess.run(
            ["git", "fetch", self.fetch_url, since_sha, "--no-tags", "--depth", "1"],
            cwd=self.worktree_path,
            capture_output=True,
            env=env,
        )
        if fetch.returncode != 0:
            logger.warning(f"could not fetch previously reviewed commit {since_sha}, falling back to full review")
            return None

        diff = subprocess.run(
            ["git", "diff", since_sha, "HEAD"],
            cwd=self.worktree_path,
            capture_output=True,
            text=True,
            env=env,
        )
        if diff.returncode != 0:
            logger.warning(f"git diff against {since_sha} failed, falling back to full review")
            return None
        return diff.stdout

    def get_gitignore_spec(self) -> pathspec.PathSpec:
        patterns: list[str] = []

        if not self.worktree_path:
            return pathspec.PathSpec.from_lines("gitwildmatch", patterns)

        result = subprocess.run(
            ["git", "ls-files", ".gitignore", "**/.gitignore"],
            cwd=self.worktree_path,
            capture_output=True,
            text=True,
            check=True,
        )

        gitignore_files = [os.path.join(self.worktree_path, f.strip()) for f in result.stdout.split("\n") if f.strip()]

        for gitignore_path in gitignore_files:
            try:
                with open(gitignore_path, encoding="utf-8", errors="ignore") as f:
                    patterns.extend(line.strip() for line in f if line.strip() and not line.startswith("#"))
            except Exception:
                continue
        return pathspec.PathSpec.from_lines("gitwildmatch", patterns)
