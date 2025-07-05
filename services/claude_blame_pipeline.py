import asyncio
import logging
import os

from libs import constants, llmFactory
from libs.helpers import cosine_similarity
from libs.prompt_templates.culprit_pull_request_with_score import blame_prompt, culprit_parser
from libs.sqlite.core.core_sqlite_client import Database
from models.models import CulpritPullRequests, Issue, PullRequest, PullRequestWithScore
from services.github import comment_service, issue_service, pull_request_service

logger = logging.getLogger(__name__)
ai_env = os.getenv("LLM_TYPE", "open-ai")  # Get the LLM type from environment variable


async def run(issue_id: int, db: Database):
    try:
        yield "starting blame pipeline"
        is_processed = db.get_issue_processed_status(issue_id)
        if is_processed:
            yield "issue is already processed. skipping blame pipeline."
            logger.info(f"{issue_id}: already processed.")
            return

        issue = await issue_service.add_issue(issue_id, db)
        logger.info(f"{issue_id}: added to database")

        if constants.LABELS["DeployBlockerCash"] not in issue.labels:
            yield f"issue is not labeled with {constants.LABELS['DeployBlockerCash']}. skipping blame pipeline."
            logger.info(f"{issue_id}: not labeled with {constants.LABELS['DeployBlockerCash']}.")
            return

        task_add_pulls = asyncio.create_task(
            asyncio.to_thread(
                pull_request_service.add_new_pull_requests_between,
                base="production",
                head="staging",
                issue_id=issue_id,
                db=db,
            )
        )

        while not task_add_pulls.done():
            await asyncio.sleep(10)
            yield "this might take a minute. fetching pull requests..."  # heartbeat to avoid closing the thread

        await task_add_pulls

        pull_requests = db.get_pull_requests_for_issue(issue_id)
        if not pull_requests or len(pull_requests) == 0:
            logger.info(f"{issue_id}: no pull requests found to process")
            yield "no pull requests found to process."
            return

        logger.info(f"{issue_id}: found {len(pull_requests)} pull requests in staging")

        pull_requests_without_cp = [pr for pr in pull_requests if "cp staging" not in pr.title.lower()]
        logger.info(f"{issue_id}: found {len(pull_requests_without_cp)} pull requests without 'cp staging'")

        prs_with_scores = _add_pull_request_semantic_score(issue, pull_requests_without_cp, db=db)
        if not prs_with_scores or len(prs_with_scores) == 0:
            logger.info(f"{issue_id}: no pull requests with semantic scores found")
            yield "no culprit pull requests found."
            return

        logger.info(f"{issue_id}: found {len(prs_with_scores)} pull requests with semantic scores")
        yield "finding culprit pull requests"

        tasks_culprit_pull_requests = [
            asyncio.create_task(
                _culprit_task(
                    page=0,
                    culprits_to_find=2,
                    issue=issue,
                    prs_with_scores=prs_with_scores,
                )
            ),  # Top PRs
            asyncio.create_task(
                _culprit_task(
                    page=1,
                    culprits_to_find=1,
                    issue=issue,
                    prs_with_scores=prs_with_scores,
                )
            ),  # Exploratory PRs
        ]

        # heartbeat until both tasks are done to avoid thread being killed by timeout
        while any(not t.done() for t in tasks_culprit_pull_requests):
            await asyncio.sleep(10)
            yield "this might take a minute. ranking pull requests..."

        top_prs, exploratory_prs = [t.result() for t in tasks_culprit_pull_requests]
        culprit_pull_requests = [pr for batch in (top_prs, exploratory_prs) if batch for pr in batch.pull_requests]
        if not culprit_pull_requests or len(culprit_pull_requests) == 0:
            logger.info(f"{issue_id}: no culprit pull requests found")
            yield "no culprit pull requests found"
            return

        logger.info(f"{issue_id}: found {len(culprit_pull_requests)} culprit pull requests")

        yield "found culprit pull requests for the issue."
        comment = await comment_service.add_comment(issue_number=issue.id, culprit_pull_requests=culprit_pull_requests)
        logger.info(f"{issue_id}: added comment to the issue {comment}")
        yield "added comment to the issue."

        db.update_issue_processed_and_result(issue.id, True, culprit_pull_requests)
        logger.info(f"{issue_id}: blame pipeline completed successfully")
        yield "blame pipeline completed successfully!"
    except Exception as e:
        logger.error(f"{issue_id}: error in blame pipeline {e}")
        yield f"some error occurred in blame pipeline. please report this issue with the issue id: {issue_id}"


async def _culprit_task(page, culprits_to_find, issue, prs_with_scores):
    return await asyncio.to_thread(
        _find_culprit_pull_requests,
        page=page,
        culprits_to_find=culprits_to_find,
        issue=issue,
        pull_requests=prs_with_scores,
    )


def _add_pull_request_semantic_score(
    issue: Issue, pull_requests: list[PullRequest], db: Database
) -> list[PullRequestWithScore]:
    scored_prs: list[PullRequestWithScore] = [
        PullRequestWithScore(pull_request=pr, score=cosine_similarity(issue.embedding, pr.embedding))
        for pr in pull_requests
    ]

    for _, pr in enumerate(scored_prs):
        db.update_issue_pull_request_score(issue_id=issue.id, pull_request_id=pr.pull_request.id, score=pr.score)

    return scored_prs if scored_prs else []


# Page is a zero-based index, so page 0 means the first 20 items.
# culprits_to_find is the number of pull requests to return.
def _find_culprit_pull_requests(
    page: int,
    culprits_to_find: int,
    issue: Issue,
    pull_requests: list[PullRequestWithScore],
) -> CulpritPullRequests | None:
    pull_requests_sorted_by_score = sorted(pull_requests, key=lambda x: x.score, reverse=True)

    max_items = 20
    start_index = page * max_items

    selected_pull_requests = pull_requests_sorted_by_score[start_index : start_index + max_items]
    if not selected_pull_requests or len(selected_pull_requests) == 0:
        logger.info(f"{issue.id}: no pull requests found for page {page}")
        return None

    pr_block = _format_pull_requests(selected_pull_requests)
    input = blame_prompt.format(
        issue_id=issue.id,
        issue_title=issue.title,
        issue_steps=issue.steps,
        culprits_to_find=culprits_to_find,
        pull_requests_block=pr_block,
    )
    llmReasoning = llmFactory.llmFactory().getLLM(
        ai_env, False, constants.ModelThinkingType.REASONING, constants.ModelCostType.STANDARD
    )

    response = llmReasoning.invoke(input)
    return culprit_parser.invoke(response)


def _format_pull_requests(prs: list[PullRequestWithScore]) -> str:
    return "\n\n".join(
        f"""PR id #{pr.pull_request.id}

Title: {pr.pull_request.title}

Test Steps: {pr.pull_request.test.strip() if pr.pull_request.test else "No test steps provided."}

Files Changed: {", ".join(pr.pull_request.files) if pr.pull_request.files else "No files listed."}

Code diff summary: {pr.pull_request.code_diff_summary if pr.pull_request.code_diff_summary else "No code diff summary provided."}

Score: {pr.score:.2f}

Explanation: {pr.pull_request.explaination.strip() if pr.pull_request.explaination else "No explanation provided."}"""
        for pr in prs
    )
