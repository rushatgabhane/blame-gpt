import logging
import os

from github import Auth, Github
from github.GithubRetry import GithubRetry
from pydantic import SecretStr

logger = logging.getLogger(__name__)

_app_auth: Auth.AppAuth | None = None


def _get_app_auth() -> Auth.AppAuth:
    """GitHub App auth, created lazily so a Bitbucket-only deployment can run without GitHub credentials."""
    global _app_auth
    if _app_auth:
        return _app_auth

    app_id = os.getenv("GITHUB_APP_ID") or ""
    private_key = SecretStr(os.getenv("GITHUB_APP_PRIVATE_KEY") or "")
    if not app_id or not private_key.get_secret_value():
        raise RuntimeError("GITHUB_APP_ID and GITHUB_APP_PRIVATE_KEY environment variables must be set")

    _app_auth = Auth.AppAuth(app_id, private_key.get_secret_value())
    logger.info("GitHub App initialized")
    return _app_auth


def get_github_client(installation_id: int):
    """Create GitHub client for a specific installation."""
    installation_auth = Auth.AppInstallationAuth(_get_app_auth(), installation_id)
    # Limit to 1 retry max to prevent duplicate write operations
    retry = GithubRetry(total=1)
    gh_client = Github(auth=installation_auth, retry=retry)
    return gh_client


def get_installation_token(installation_id: int):
    """Get installation token for a specific installation."""
    installation_auth = Auth.AppInstallationAuth(_get_app_auth(), installation_id)
    Github(auth=installation_auth)  # do this to avoid init errors
    return installation_auth.token
