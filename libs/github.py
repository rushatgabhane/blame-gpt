import logging
import os
from typing import cast

from github import Github
from github.AuthenticatedUser import AuthenticatedUser
from pydantic import SecretStr

from libs import constants

github_token = SecretStr(os.getenv("GITHUB_TOKEN") or "")
gh = Github(github_token.get_secret_value())

repo = gh.get_repo(f"{constants.REPO_OWNER}/{constants.REPO_NAME}")
rate = gh.get_rate_limit()
gh_user: AuthenticatedUser = cast(AuthenticatedUser, gh.get_user())

logging.info("repo initialized as %s", repo.full_name)
logging.info("rate limit information: %s", rate)
logging.info("user information: %s", gh_user)
