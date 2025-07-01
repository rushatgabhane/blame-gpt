import os
from github import Github
from libs import constants
from libs.rate_limiter import rate_limited_github
import logging

# Initialize GitHub client
gh = Github(os.getenv("GITHUB_TOKEN"))


# Wrap repo methods with rate limiting
class RateLimitedRepo:
    def __init__(self, github_repo):
        self._repo = github_repo

    def __getattr__(self, name):
        attr = getattr(self._repo, name)
        if callable(attr) and name in ["get_pull", "get_pulls", "compare", "get_contents", "get_commits", "get_issues"]:
            return rate_limited_github(attr)
        return attr


# Initialize repo with rate limiting
try:
    _base_repo = gh.get_repo(f"{constants.REPO_OWNER}/{constants.REPO_NAME}")
    repo = RateLimitedRepo(_base_repo)
    rate = gh.get_rate_limit()
    logging.info("GitHub repo initialized as %s", _base_repo.full_name)
    logging.info("GitHub rate limit information: %s", rate)
except Exception as e:
    logging.warning(f"Failed to initialize GitHub repo (this is expected in test environments): {e}")

    # Create a mock repo for testing environments
    class MockRepo:
        full_name = f"{constants.REPO_OWNER}/{constants.REPO_NAME}"

        def get_pull(self, number):
            raise NotImplementedError("Mock repo - GitHub token required")

        def compare(self, base, head):
            raise NotImplementedError("Mock repo - GitHub token required")

    repo = MockRepo()
