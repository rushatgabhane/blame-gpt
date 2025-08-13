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
from github.Repository import Repository

from libs.github import get_installation_token

logger = logging.getLogger(__name__)


class LocalRepository:
    """
    Context manager for local repository operations with automatic cleanup.

    Features:
    - Clones GitHub PR branches (same-repo and forks)
    - Uses efficient shallow cloning + git worktrees
    - Race condition protection with file locking
    - Path injection prevention with sanitization
    - File system operations (gitignore, file reading, etc.)
    - Guaranteed cleanup on success, failure, or exception
    - Returns None if repo/branch names are invalid

    Usage:
        with LocalRepository(pr_id, repo) as local_repo:
            if local_repo is None:
                continue
            # Use local_repo.worktree_path for file operations
        # Automatic cleanup after out of scope
    """

    def __init__(self, pull_request_id: int, repo: Repository, installation_id: int):
        self.pull_request_id = pull_request_id
        self.repo = repo
        self.installation_id = installation_id
        self.clone_path: str | None = None
        self.worktree_path: str | None = None
        self.git_config_dir = tempfile.TemporaryDirectory(prefix="gitcfg-")
        self.askpass_script_path = self._create_askpass_script()

    def __enter__(self):
        try:
            pr = self.repo.get_pull(self.pull_request_id)
            repo_to_clone = pr.base.repo

            clone_url = f"https://github.com/{repo_to_clone.full_name}.git"

            sanitized_branch = pr.head.ref.replace("/", "-")
            local_branch_name = f"pr-{pr.number}-{sanitized_branch}"

            base_name = f"blamegpt-{self.repo.full_name}"
            worktree_name = f"blamegpt-{pr.number}-{sanitized_branch}"

            self.clone_path = self._safe_temp_path(base_name)
            self.worktree_path = self._safe_temp_path(worktree_name)

            if not self.clone_path or not self.worktree_path:
                return None

            self._create_or_update_clone(clone_url, local_branch_name)
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
        token = get_installation_token(self.installation_id)
        askpass_script = f"""#!/bin/bash
if [[ "$1" == *"Username"* ]]; then
    echo "x-access-token"
else
    echo "{token}"
fi
"""
        askpass_path = Path(self.git_config_dir.name) / "git-askpass.sh"
        with open(askpass_path, "w") as f:
            f.write(askpass_script)
        askpass_path.chmod(0o700)

        return str(askpass_path)

    def _create_or_update_clone(self, clone_url: str, branch_name: str):
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

            fetch_cmd = ["git", "remote", "set-url", "origin", clone_url]
            subprocess.run(fetch_cmd, cwd=self.clone_path, check=True, capture_output=True, env=env)

            refspec = f"pull/{self.pull_request_id}/head:refs/heads/{branch_name}"
            fetch_pr_branch_cmd = ["git", "fetch", "origin", refspec, "--force", "--no-tags"]
            subprocess.run(fetch_pr_branch_cmd, cwd=self.clone_path, check=True, capture_output=True, env=env)

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
        with contextlib.suppress(Exception):
            self.git_config_dir.cleanup()

        if not self.worktree_path or not self.clone_path:
            return

        cleanup_worktree_path = self.worktree_path
        self.worktree_path = None

        try:
            logger.info("cleaning up worktree")
            subprocess.run(
                ["git", "worktree", "remove", cleanup_worktree_path, "--force"],
                cwd=self.clone_path,
                capture_output=True,
            )
        except Exception:
            if not os.path.exists(cleanup_worktree_path):
                return
            shutil.rmtree(cleanup_worktree_path)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._cleanup()

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
