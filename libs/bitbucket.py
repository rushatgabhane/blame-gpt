import os

import requests

API_BASE = "https://api.bitbucket.org/2.0"


def get_access_token() -> str:
    return os.getenv("BITBUCKET_ACCESS_TOKEN", "")


def _headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {get_access_token()}"}


def _pr_url(workspace: str, repo: str, pull_request_id: int) -> str:
    return f"{API_BASE}/repositories/{workspace}/{repo}/pullrequests/{pull_request_id}"


def get_pull_request(workspace: str, repo: str, pull_request_id: int) -> dict:
    response = requests.get(_pr_url(workspace, repo, pull_request_id), headers=_headers(), timeout=30)
    response.raise_for_status()
    return response.json()


def get_pull_request_diff(workspace: str, repo: str, pull_request_id: int) -> str:
    response = requests.get(f"{_pr_url(workspace, repo, pull_request_id)}/diff", headers=_headers(), timeout=60)
    response.raise_for_status()
    return response.text


def get_pull_request_diffstat(workspace: str, repo: str, pull_request_id: int) -> list[dict]:
    url: str | None = f"{_pr_url(workspace, repo, pull_request_id)}/diffstat"
    stats: list[dict] = []
    while url:
        response = requests.get(url, headers=_headers(), timeout=30)
        response.raise_for_status()
        page = response.json()
        stats.extend(page.get("values", []))
        url = page.get("next")
    return stats


def get_pull_request_comment(workspace: str, repo: str, pull_request_id: int, comment_id: int) -> dict:
    url = f"{_pr_url(workspace, repo, pull_request_id)}/comments/{comment_id}"
    response = requests.get(url, headers=_headers(), timeout=30)
    response.raise_for_status()
    return response.json()


def add_pull_request_comment(
    workspace: str, repo: str, pull_request_id: int, markdown: str, path: str | None = None, line: int | None = None
) -> None:
    payload: dict = {"content": {"raw": markdown}}
    if path:
        payload["inline"] = {"path": path, "to": line}

    url = f"{_pr_url(workspace, repo, pull_request_id)}/comments"
    response = requests.post(url, json=payload, headers=_headers(), timeout=30)
    response.raise_for_status()
