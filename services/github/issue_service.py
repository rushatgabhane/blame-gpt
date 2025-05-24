import requests
import libs.constants as constants
import logging
import re
import os
from models.issue import Issue

logger = logging.getLogger(__name__)


async def get_issue(owner: str, repo: str, issue_number: int) -> Issue:
    query = """
    query ($owner: String!, $repo: String!, $issueNumber: Int!) {
        repository(owner: $owner, name: $repo) {
            issue(number: $issueNumber) {
                title
                body
                labels(first: 10) {
                    nodes {
                        name
                    }
                }
            }
        }
    }
    """

    variables = {"owner": owner, "repo": repo, "issueNumber": issue_number}

    headers = {
        "Authorization": f"Bearer {os.getenv('GITHUB_TOKEN')}",
        "Content-Type": "application/json",
    }

    response = requests.post(
        constants.GITHUB_API_URL,
        json={"query": query, "variables": variables},
        headers=headers,
    )

    response_json = response.json()
    if "errors" in response_json:
        logging.error(f"GraphQL error: {response_json['errors']}")
        raise RuntimeError(f"GitHub GraphQL error: {response_json['errors']}")

    if response.status_code != 200:
        logging.error(
            f"Failed to fetch issue: {issue_number} {response.status_code} - {response.text}"
        )
        return RuntimeError(
            f"Failed to fetch issue: {issue_number} {response.status_code} - {response.text}"
        )

    issue = response_json["data"]["repository"]["issue"]

    isDeployBlocker = False
    for label in issue["labels"]["nodes"]:
        if label["name"] == constants.LABELS["DeployBlockerCash"]:
            isDeployBlocker = True
            break

    if not isDeployBlocker:
        logging.info(f"DeployBlockerCash label not found in issue: {issue_number}")
        return None

    steps = extract_steps_from_description(issue["body"])

    return Issue(
        id=issue_number,
        title=issue["title"],
        steps=steps,
        raw_body=issue["body"],
        labels=[label["name"] for label in issue["labels"]["nodes"]],
    )


def extract_steps_from_description(description: str) -> str:
    pattern = r"""
        \#\#\s*Action\s*Performed:\s*
        .*?
        \#\#\s*Expected\s*Result:\s*
        .*?
        \#\#\s*Actual\s*Result:\s*
        .*?
        (?=\#\#\s*Workaround:)
    """

    match = re.search(pattern, description, re.DOTALL | re.VERBOSE | re.IGNORECASE)
    if match:
        return match.group(0).strip()
    else:
        logging.warning("No steps found in the description: {description}")
        return ""
