import logging
import re

from libs import llmFactory, modeltypeenums
from libs.github import repo
from libs.sqlite.core.core_sqlite_client import Database
from models.models import Issue

logger = logging.getLogger(__name__)


async def add_issue(issue_id: int, db: Database) -> Issue:
    try:
        gh_issue = repo.get_issue(number=issue_id)
        labels = [label.name for label in gh_issue.labels] or []
        steps = extract_steps_from_description(gh_issue.body or "")
        title = gh_issue.title or ""
        embedding_model = llmFactory.llmFactory().getLLM(
            modelType=modeltypeenums.ModelThinkingType.EMBEDDING, cost=modeltypeenums.ModelCostType.STANDARD
        )
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


def get_all_issues(db: Database) -> list[Issue]:
    return db.get_all_issues()
