import libs.constants as constants
import logging
from models.models import Issue, PullRequest, CulpritPullRequests
from libs.sqlite.sqlite_client import Database
from typing import List
from libs.prompt_templates.culprit_pull_request import blame_prompt, culprit_parser
from libs.llm import llm

logger = logging.getLogger(__name__)


def get_culprit_pull_requests(issue: Issue, db: Database) -> CulpritPullRequests | None:
    logger.info(f"Getting culprit pull requests for issue {issue.id}")
    pull_requests = db.get_pull_requests_for_issue(issue.id)

    if not pull_requests:
        logger.info(f"no pull requests found for issue {issue.id}")
        return None

    pull_requests_without_cp = [
        pr for pr in pull_requests if "cp staging" not in pr.title.lower()
    ]

    logger.info(f"Found {len(pull_requests_without_cp)} pull requests without 'cp staging' for issue {issue.id}")

    culprit_prs = rank_pull_requests(issue, pull_requests_without_cp)
    logger.info(f"Found culprit pull requests for issue {issue.id}")

    return culprit_prs


def rank_pull_requests(
    issue: Issue, pull_requests: List[PullRequest]
) -> CulpritPullRequests:
    logger.info(f"ranking pull requests for issue {issue.id}")
    pr_block = format_pull_requests(pull_requests)
    input_data = blame_prompt.format(
        issue_id=issue.id,
        issue_title=issue.title,
        issue_steps=issue.steps,
        pull_requests_block=pr_block,
    )
    response = llm.invoke(input_data)
    return culprit_parser.parse(response.content)


def format_pull_requests(prs: List[PullRequest]) -> str:
    return "\n\n".join(
        f"""### PR #{pr.id}
Title: {pr.title}
Test Steps: {pr.test.strip() if pr.test else 'No test steps provided.'}
Explanation: {pr.explaination.strip() if pr.explaination else 'No explanation provided.'}
Files Changed: {", ".join(pr.files) if pr.files else 'No files listed.'}"""
        for pr in prs
    )
