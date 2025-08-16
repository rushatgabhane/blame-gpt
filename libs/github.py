import logging
import os

from github import Auth, Github
from github.GithubRetry import GithubRetry
from pydantic import SecretStr

logger = logging.getLogger(__name__)

# GitHub App authentication setup
github_app_id = os.getenv("GITHUB_APP_ID") or ""
github_app_private_key = SecretStr(os.getenv("GITHUB_APP_PRIVATE_KEY") or "")

if not github_app_id or not github_app_private_key.get_secret_value():
    raise RuntimeError("GITHUB_APP_ID and GITHUB_APP_PRIVATE_KEY environment variables must be set")

app_auth = Auth.AppAuth(github_app_id, github_app_private_key.get_secret_value())

logger.info("GitHub App initialized")


def get_github_client(installation_id: int):
    """Create GitHub client for a specific installation."""
    installation_auth = Auth.AppInstallationAuth(app_auth, installation_id)
    # Limit to 1 retry max to prevent duplicate write operations
    retry = GithubRetry(total=1)
    gh_client = Github(auth=installation_auth, retry=retry)
    return gh_client


def get_installation_token(installation_id: int):
    """Get installation token for a specific installation."""
    installation_auth = Auth.AppInstallationAuth(app_auth, installation_id)
    Github(auth=installation_auth)  # do this to avoid init errors
    return installation_auth.token
