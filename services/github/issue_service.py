import logging
import re

from github.Repository import Repository

from libs.llm import embedding_model
from libs.sqlite.core.core_sqlite_client import Database
from models.models import Issue

logger = logging.getLogger(__name__)


async def add_issue(issue_id: int, repo_client: Repository, db: Database) -> Issue:
    try:
        gh_issue = repo_client.get_issue(number=issue_id)
        labels = [label.name for label in gh_issue.labels] or []
        steps = _extract_steps_from_description(gh_issue.body or "")
        title = gh_issue.title or ""
        issue_embedding = embedding_model.embed_query(f"{title}\n {steps}")

        issue = Issue(
            id=gh_issue.number,
            title=title,
            steps=steps,
            raw_body=gh_issue.body or "",
            labels=labels,
            embedding=issue_embedding,
        )
        db.add_issue(issue)
        return issue
    except Exception as e:
        logger.error(f"error fetching issue #{issue_id}: {e}")
        raise


def _extract_steps_from_description(description: str) -> str:
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
        logging.warning("no steps found in the description")
        return ""


def get_all_issues(db: Database) -> list[Issue]:
    return db.get_all_issues()


async def add_issue_if_not_exists(issue_id: int, repo_client: Repository, db: Database) -> Issue | None:
    try:
        existing_issue = db.get_issue_by_id(issue_id)
        if existing_issue:
            return existing_issue
        return await add_issue(issue_id, repo_client, db)
    except Exception as e:
        logger.error(f"error fetching issue #{issue_id} from db: {e}")
        raise
