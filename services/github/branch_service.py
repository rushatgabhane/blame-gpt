import contextlib
import fcntl
import logging
import os
import re
import shutil
import subprocess
import tempfile

from github.Repository import Repository

logger = logging.getLogger(__name__)


class BranchClone:
    """
    Context manager for safely cloning GitHub PR branches with automatic cleanup.

    Features:
    - Handles both same-repo and fork PRs
    - Uses efficient shallow cloning + git worktrees
    - Race condition protection with file locking
    - Path injection prevention with sanitization
    - Guaranteed cleanup on success, failure, or exception
    - Returns None if repo/branch names are invalid

    Usage:
        with BranchClone(pr_id, repo) as clone:
            if clone is None:
                continue
            # Use clone.worktree_path for file operations
        # Automatic after out of scope
    """

    def __init__(self, pull_request_id: int, repo: Repository):
        self.pull_request_id = pull_request_id
        self.repo = repo
        self.clone_path: str | None = None
        self.worktree_path: str | None = None

    def __enter__(self):
        try:
            pr = self.repo.get_pull(self.pull_request_id)
            clone_url = pr.head.repo.clone_url if pr.head.repo.id != pr.base.repo.id else pr.base.repo.clone_url
            branch_name = pr.head.ref

            base_name = f"blamegpt-{self.repo.full_name}"
            worktree_name = f"blamegpt-{pr.number}-{branch_name}"

            self.clone_path = self._safe_temp_path(base_name)
            self.worktree_path = self._safe_temp_path(worktree_name)

            if not self.clone_path or not self.worktree_path:
                return None

            self._create_or_update_clone(clone_url, branch_name)
            self._create_worktree(branch_name)
            return self
        except Exception as e:
            logger.error(f"Failed to setup branch clone: {e}")
            self._cleanup()
            raise

    def _create_or_update_clone(self, clone_url: str, branch_name: str):
        if not self.clone_path:
            raise ValueError("Clone path not initialized")

        lock_file_path = f"{self.clone_path}.lock"

        with open(lock_file_path, "w") as lock_file:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            self._create_or_update_clone_locked(clone_url, branch_name)

        # Cleanup lock file
        with contextlib.suppress(OSError):
            os.unlink(lock_file_path)

    def _create_or_update_clone_locked(self, clone_url: str, branch_name: str):
        """Handle clone creation/update with lock already acquired"""
        if not self.clone_path:
            raise ValueError("Clone path not initialized")

        if not os.path.exists(self.clone_path):
            subprocess.run(
                ["git", "clone", "--bare", "--depth", "1", clone_url, self.clone_path], check=True, capture_output=True
            )
            logger.info(f"Created bare clone at {self.clone_path}")
            return

        subprocess.run(
            ["git", "fetch", "origin", f"{branch_name}:refs/heads/{branch_name}"],
            cwd=self.clone_path,
            check=True,
            capture_output=True,
        )
        logger.info(f"Updated clone with branch {branch_name}")

    def _create_worktree(self, branch_name: str):
        if not self.clone_path or not self.worktree_path:
            raise ValueError("Paths not initialized")

        subprocess.run(
            ["git", "worktree", "add", self.worktree_path, branch_name],
            cwd=self.clone_path,
            check=True,
            capture_output=True,
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

        cleanup_worktree_path = self.worktree_path
        self.worktree_path = None

        try:
            subprocess.run(
                ["git", "worktree", "remove", cleanup_worktree_path, "--force"],
                cwd=self.clone_path,
                capture_output=True,
            )
            logger.info(f"removed worktree {cleanup_worktree_path}")
        except Exception:
            if not os.path.exists(cleanup_worktree_path):
                return
            shutil.rmtree(cleanup_worktree_path)

    def __exit__(self, _exc_type, _exc_val, _exc_tb):
        self._cleanup()
