import os
from github import Github
from libs import constants
import logging

gh = Github(os.getenv("GITHUB_TOKEN"))
repo = gh.get_repo(f"{constants.REPO_OWNER}/{constants.REPO_NAME}")
rate = gh.get_rate_limit()

gh_secondary = Github(os.getenv("GITHUB_TOKEN_SECONDARY"))
repo_secondary = gh_secondary.get_repo(f"{constants.REPO_OWNER}/{constants.REPO_NAME}")
rate_secondary = gh_secondary.get_rate_limit()

logging.info("repo initialized as %s", repo.full_name)
logging.info("rate limit information: %s", rate)
logging.info("secondary repo initialized as %s", repo_secondary.full_name)
logging.info("secondary rate limit information: %s", rate_secondary)
