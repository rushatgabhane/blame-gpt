import logging
import os

import httpx
from github import Auth, Github
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
    gh_client = Github(auth=installation_auth)
    return gh_client


def get_installation_token(installation_id: int):
    """Get installation token for a specific installation."""
    installation_auth = Auth.AppInstallationAuth(app_auth, installation_id)
    return installation_auth.token


async def get_installation_id_for_repo(repo_owner: str, repo_name: str) -> int | None:
    try:
        jwt_token = app_auth.create_jwt()

        url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/installation"
        headers = {
            "Authorization": f"Bearer {jwt_token}",
            "Accept": "application/vnd.github.v3+json",
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=headers)

        if response.status_code == 200:
            installation_data = response.json()
            return installation_data.get("id")
        else:
            logger.error(f"Failed to get installation for {repo_owner}/{repo_name}: {response.status_code}")
            return None

    except Exception as e:
        logger.error(f"Could not find installation for {repo_owner}/{repo_name}: {e}")
        return None
