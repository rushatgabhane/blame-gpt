import asyncio
from services.github import pull_request_service, issue_service
from models.models import Issue
from libs.sqlite.sqlite_client import Database
from models.models import (
    PullRequest,
    CulpritPullRequests,
    PullRequestWithScore,
)
from libs.prompt_templates.culprit_pull_request_with_score import (
    blame_prompt,
    culprit_parser,
)
from typing import List
from libs.llm import llm
import logging
from services.github import comment_service
from libs.helpers import cosine_similarity
from libs import constants

logger = logging.getLogger(__name__)


async def run(issue_id: int, db: Database):
    try:
        yield f"starting blame pipeline"
        is_processed = db.get_issue_processed_status(issue_id)
        if is_processed:
            yield f"issue is already processed. skipping blame pipeline."
            logger.info(f"{issue_id}: already processed.")
            return

        issue = await issue_service.add_issue(issue_id, db)
        logger.info(f"{issue_id}: added to database")

        if constants.LABELS["DeployBlockerCash"] not in issue.labels:
            yield f"issue is not labeled with {constants.LABELS["DeployBlockerCash"]}. skipping blame pipeline."
            logger.info(f"{issue_id}: not labeled with {constants.LABELS['DeployBlockerCash']}.")
            return

        await asyncio.to_thread(
            pull_request_service.add_new_pull_requests_between,
            base="production",
            head="staging",
            issue_id=issue_id,
            db=db,
        )

        pull_requests = db.get_pull_requests_for_issue(issue_id)
        if not pull_requests or len(pull_requests) == 0:
            logger.info(f"{issue_id}: no pull requests found to process")
            yield f"no pull requests found to process."
            return

        logger.info(f"{issue_id}: found {len(pull_requests)} pull requests in staging")

        pull_requests_without_cp = [pr for pr in pull_requests if "cp staging" not in pr.title.lower()]
        logger.info(f"{issue_id}: found {len(pull_requests_without_cp)} pull requests without 'cp staging'")

        prs_with_scores = add_pull_request_semantic_score(issue, pull_requests_without_cp, db=db)
        if not prs_with_scores or len(prs_with_scores) == 0:
            logger.info(f"{issue_id}: no pull requests with semantic scores found")
            yield f"no culprit pull requests found."
            return

        logger.info(f"{issue_id}: found {len(prs_with_scores)} pull requests with semantic scores")

        yield f"finding culprit pull requests"
        culprit_pull_requests = await asyncio.to_thread(find_culprit_pull_requests, issue, prs_with_scores)
        if not culprit_pull_requests or not culprit_pull_requests.pull_requests:
            logger.info(f"{issue_id}: no culprit pull requests found")
            yield f"no culprit pull requests found"
            return

        logger.info(f"{issue_id}: found {len(culprit_pull_requests.pull_requests)} culprit pull requests")

        yield f"found culprit pull requests for the issue."
        comment = await comment_service.add_comment(issue_number=issue.id, culprit_pull_requests=culprit_pull_requests)
        logger.info(f"{issue_id}: added comment to the issue {comment}")
        yield f"added comment to the issue."

        db.update_issue_processed_and_result(issue.id, True, culprit_pull_requests.pull_requests)
        logger.info(f"{issue_id}: blame pipeline completed successfully")
        yield f"blame pipeline completed successfully!"
    except Exception as e:
        logger.error(f"{issue_id}: error in blame pipeline {e}")
        yield f"some error occurred in blame pipeline. please report this issue with the issue id: {issue_id}"


def add_pull_request_semantic_score(
    issue: Issue, pull_requests: List[PullRequest], db: Database
) -> List[PullRequestWithScore]:
    scored_prs: List[PullRequestWithScore] = [
        PullRequestWithScore(pull_request=pr, score=cosine_similarity(issue.embedding, pr.embedding))
        for pr in pull_requests
    ]

    for i, pr in enumerate(scored_prs):
        db.update_issue_pull_request_score(issue_id=issue.id, pull_request_id=pr.pull_request.id, score=pr.score)

    return scored_prs if scored_prs else []


def find_culprit_pull_requests(issue: Issue, pull_requests: List[PullRequestWithScore]) -> CulpritPullRequests | None:
    top_n = 15
    top_n_pull_requests = sorted(pull_requests, key=lambda x: x.score, reverse=True)[
        : top_n if len(pull_requests) > top_n else len(pull_requests)
    ]

    pr_block = format_pull_requests(top_n_pull_requests)
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


def format_pull_requests(prs: List[PullRequestWithScore]) -> str:
    return "\n\n".join(
        f"""PR id #{pr.pull_request.id}

Title: {pr.pull_request.title}

Test Steps: {pr.pull_request.test.strip() if pr.pull_request.test else 'No test steps provided.'}

Files Changed: {", ".join(pr.pull_request.files) if pr.pull_request.files else 'No files listed.'}

Score: {pr.score:.2f}

Explanation: {pr.pull_request.explaination.strip() if pr.pull_request.explaination else 'No explanation provided.'}"""
        for pr in prs
    )
