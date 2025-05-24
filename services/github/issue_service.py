import libs.constants as constants
import logging
import re
from models.models import Issue
from libs.github import repo
from libs.sqlite.sqlite_client import Database
from typing import List

logger = logging.getLogger(__name__)


async def add_issue(issue_number: int, db: Database) -> Issue:
    try:
        gh_issue = repo.get_issue(number=issue_number)

        labels = [label.name for label in gh_issue.labels]
        if constants.LABELS["DeployBlockerCash"] not in labels:
            logger.info(f"DeployBlockerCash label not found in issue: {issue_number}")
            return None

        steps = extract_steps_from_description(gh_issue.body or "")

        issue = Issue(
            id=gh_issue.number,
            title=gh_issue.title,
            steps=steps,
            raw_body=gh_issue.body or "",
            labels=labels,
        )
        db.add_issue(issue)
        return issue
    except Exception as e:
        logger.error(f"Error fetching issue #{issue_number}: {e}")
        raise


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


def get_all_issues(db: Database) -> List[Issue]:
    return db.get_all_issues()
