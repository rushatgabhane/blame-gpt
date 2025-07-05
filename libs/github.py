import logging
import os

from github import Github

from libs import constants

github_token = os.getenv("GITHUB_TOKEN")

if not github_token:
    raise Exception("GitHub token not found. Make sure to set the `GITHUB_TOKEN` environment variable")

gh = Github(github_token)

repo = gh.get_repo(f"{constants.REPO_OWNER}/{constants.REPO_NAME}")
rate = gh.get_rate_limit()

logging.info("secondary repo initialized as %s", repo.full_name)
logging.info("secondary rate limit information: %s", rate)
