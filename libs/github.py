import logging
import os
from typing import cast

from github import Github
from github.AuthenticatedUser import AuthenticatedUser

from libs import constants

github_token = os.getenv("GITHUB_TOKEN")

if not github_token:
    raise Exception("GitHub token not found. Make sure to set the `GITHUB_TOKEN` environment variable")

gh = Github(github_token)

repo = gh.get_repo(f"{constants.REPO_OWNER}/{constants.REPO_NAME}")
rate = gh.get_rate_limit()
gh_user: AuthenticatedUser = cast(AuthenticatedUser, gh.get_user())

logging.info("repo initialized as %s", repo.full_name)
logging.info("rate limit information: %s", rate)
logging.info("user information: %s", gh_user)
