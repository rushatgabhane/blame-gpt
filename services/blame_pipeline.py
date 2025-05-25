import asyncio
from services.github import pull_request_service
from models.models import Issue
from libs.sqlite.sqlite_client import Database
from typing import AsyncGenerator
from models.models import PullRequest, CulpritPullRequests
from libs.prompt_templates.culprit_pull_request import blame_prompt, culprit_parser
from typing import List
from libs.llm import llm
import logging
from services.github import comment_service

logger = logging.getLogger(__name__)


async def run_blame_pipeline(issue: Issue, db: Database):
    try:
        db_issue = db.get_issue_by_id(issue.id)
        if db_issue is not None and db_issue.is_processed:
            yield f"issue already processed"
            return

        yield "fetching new pull requests"
        await asyncio.to_thread(
            pull_request_service.add_new_pull_requests,
            base="production",
            head="staging",
            issue_number=issue.id,
            db=db,
        )

        pull_requests = db.get_pull_requests_for_issue(issue.id)
        if not pull_requests or len(pull_requests) == 0:
            yield f"no pull requests found"
            return

        yield f"found {len(pull_requests)} pull requests on staging but not on production."

        pull_requests_without_cp = [
            pr for pr in pull_requests if "cp staging" not in pr.title.lower()
        ]
        yield f"found {len(pull_requests_without_cp)} pull requests after filtering 'cp staging'."

        yield f"ranking pull requests"
        culprit_pull_requests = await asyncio.to_thread(
            rank_pull_requests, issue, pull_requests
        )
        if not culprit_pull_requests:
            yield f"no culprits found"
            return

        comment = await comment_service.add_comment(
            issue_number=issue.id, culprit_pull_requests=culprit_pull_requests
        )
        yield f"comment added {comment}"

        db.update_issue_processed_and_result(
            issue.id, True, culprit_pull_requests.pull_requests
        )
        yield f"blame pipeline completed"
    except Exception as e:
        logger.error(f"error in blame pipeline for issue {issue.id}: {e}")
        yield f"error in blame pipeline: {e}"


def rank_pull_requests(
    issue: Issue, pull_requests: List[PullRequest]
) -> CulpritPullRequests | None:
    logger.info(f"ranking pull requests for issue {issue.id}")
    pr_block = format_pull_requests(pull_requests)
    input_data = blame_prompt.format(
        issue_id=issue.id,
        issue_title=issue.title,
        issue_steps=issue.steps,
        pull_requests_block=pr_block,
    )
    response = llm.invoke(input_data)
    content = response.content
    if isinstance(content, str):
        return culprit_parser.parse(content)
    elif isinstance(content, list):
        return culprit_parser.parse(str(content))
    else:
        logger.error("Unexpected response content type: %s", type(content))
        return None


def format_pull_requests(prs: List[PullRequest]) -> str:
    return "\n\n".join(
        f"""### PR #{pr.id}
Title: {pr.title}
Test Steps: {pr.test.strip() if pr.test else 'No test steps provided.'}
Explanation: {pr.explaination.strip() if pr.explaination else 'No explanation provided.'}
Files Changed: {", ".join(pr.files) if pr.files else 'No files listed.'}"""
        for pr in prs
    )
