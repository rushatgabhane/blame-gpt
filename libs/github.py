import os
from github import Github
from libs import constants
import logging

gh = Github(os.getenv("GITHUB_TOKEN"))
repo = gh.get_repo(f"{constants.REPO_OWNER}/{constants.REPO_NAME}")
rate = gh.get_rate_limit()

logging.info("repo initialized as %s", repo.full_name)
logging.info("rate limit information: %s", rate)
