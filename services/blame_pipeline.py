import asyncio
import logging
from collections.abc import AsyncGenerator

from github.IssueComment import IssueComment
from github.Repository import Repository

from libs import constants
from libs.helpers import cosine_similarity, thinking_verb
from libs.llm import ModelNames, llm
from libs.prompt_templates.culprit_pull_request_with_score import blame_prompt, culprit_parser
from libs.sqlite.core.core_sqlite_client import Database
from models.models import CulpritPullRequests, Issue, PullRequest, PullRequestWithScore
from services.github import comment_service, issue_service, pull_request_service
from services.user_service import track_llm_usage

logger = logging.getLogger(__name__)


async def run(
    issue_id: int,
    repo_client: Repository,
    db: Database,
    usage_log_id: int | None = None,
    thinking_comment: IssueComment | None = None,
) -> AsyncGenerator[str]:
    try:
        yield "starting the blame pipeline..."

        is_processed = db.get_issue_processed_status(issue_id)
        if is_processed:
            yield "this issue is already processed. Skipping blame pipeline."
            logger.info(f"{issue_id}: already processed.")
            comment_service.edit_comment(thinking_comment, "This issue is already processed. Skipping blame.")
            return

        issue = await issue_service.add_issue(issue_id, repo_client, db)
        logger.info(f"{issue_id}: added to database")

        if constants.LABELS["DeployBlockerCash"] not in issue.labels:
            yield f"this issue is not labeled with {constants.LABELS['DeployBlockerCash']}. Skipping blame pipeline."
            logger.info(f"{issue_id}: not labeled with {constants.LABELS['DeployBlockerCash']}.")
            comment_service.edit_comment(
                thinking_comment,
                f"This issue is not labeled with {constants.LABELS['DeployBlockerCash']}. Skipping blame.",
            )
            return

        task_add_pulls = asyncio.create_task(
            asyncio.to_thread(
                pull_request_service.add_new_pull_requests_between,
                base="production",
                head="staging",
                issue_id=issue_id,
                repo_client=repo_client,
                db=db,
                usage_log_id=usage_log_id,
            )
        )

        while not task_add_pulls.done():
            await asyncio.sleep(5)
            yield f"{thinking_verb()} pull requests... this might take a minute."  # heartbeat to avoid closing the connection

        await task_add_pulls

        pull_requests = db.get_pull_requests_for_issue(issue_id)
        if not pull_requests or len(pull_requests) == 0:
            logger.info(f"{issue_id}: no pull requests found to process")
            yield "no pull requests were found to process."
            comment_service.edit_comment(thinking_comment, "❌ No pull requests were found to process.")
            return

        logger.info(f"{issue_id}: found {len(pull_requests)} pull requests in staging")

        pull_requests_without_cp = [pr for pr in pull_requests if "cp staging" not in pr.title.lower()]
        logger.info(f"{issue_id}: found {len(pull_requests_without_cp)} pull requests without 'cp staging'")

        prs_with_scores = _add_pull_request_semantic_score(issue, pull_requests_without_cp, db=db)
        if not prs_with_scores or len(prs_with_scores) == 0:
            logger.info(f"{issue_id}: no pull requests with semantic scores found")
            yield "no culprit pull requests were found."
            comment_service.edit_comment(thinking_comment, "❌ No culprit pull requests were found.")
            return

        logger.info(f"{issue_id}: found {len(prs_with_scores)} pull requests with semantic scores")
        yield "finding culprit pull requests..."

        tasks_culprit_pull_requests = [
            asyncio.create_task(
                _culprit_task(
                    page=0,
                    culprits_to_find=3,
                    issue=issue,
                    prs_with_scores=prs_with_scores,
                    db=db,
                    usage_log_id=usage_log_id,
                )
            )
        ]

        # heartbeat until both tasks are done to avoid thread being killed by timeout
        while any(not t.done() for t in tasks_culprit_pull_requests):
            await asyncio.sleep(5)
            yield "ranking pull requests... this might take a minute."

        top_prs = [t.result() for t in tasks_culprit_pull_requests]
        culprit_pull_requests = [pr for batch in (top_prs) if batch for pr in batch.pull_requests]
        if not culprit_pull_requests or len(culprit_pull_requests) == 0:
            logger.info(f"{issue_id}: no culprit pull requests found")
            yield "no culprit pull requests were found. unfortunately."
            comment_service.edit_comment(thinking_comment, "❌ No culprit pull requests were found. Unfortunately.")
            return

        logger.info(f"{issue_id}: found {len(culprit_pull_requests)} culprit pull requests")

        yield f"{thinking_verb()} culprit pull requests for this issue."

        # Update thinking comment with result, or add new comment if no thinking comment
        if thinking_comment:
            result_comment = comment_service.format_blame_comment(culprit_pull_requests)
            comment_service.edit_comment(thinking_comment, result_comment)
        else:
            await comment_service.add_comment(
                issue_number=issue.id, culprit_pull_requests=culprit_pull_requests, repo_client=repo_client
            )

        yield "Added a comment on the issue."

        db.update_issue_processed_and_result(issue.id, True, culprit_pull_requests)
        logger.info(f"{issue_id}: blame pipeline completed successfully")
        yield "Celebrating! Blame pipeline completed."
    except Exception as e:
        logger.exception(f"{issue_id}: error in blame pipeline {e}")
        yield f"some error occurred in blame pipeline. please report this issue with the issue id: {issue_id}"
        if thinking_comment:
            comment_service.edit_comment(
                thinking_comment,
                f"❌ Error occurred in blame pipeline. Please report this issue with the issue id: {issue_id}",
            )


async def _culprit_task(page, culprits_to_find, issue, prs_with_scores, db, usage_log_id):
    return await asyncio.to_thread(
        _find_culprit_pull_requests,
        page=page,
        culprits_to_find=culprits_to_find,
        issue=issue,
        pull_requests=prs_with_scores,
        db=db,
        usage_log_id=usage_log_id,
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


# Page is a zero-based index, so page 0 means the first N items.
# culprits_to_find is the number of pull requests to return.
def _find_culprit_pull_requests(
    page: int,
    culprits_to_find: int,
    issue: Issue,
    pull_requests: list[PullRequestWithScore],
    db: Database,
    usage_log_id: int | None = None,
) -> CulpritPullRequests | None:
    pull_requests_sorted_by_score = sorted(pull_requests, key=lambda x: x.score, reverse=True)

    max_items = 25
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
    response = llm.invoke(input)
    track_llm_usage(db, usage_log_id, response, ModelNames.GPT_5)
    return culprit_parser.invoke(response)


def _format_pull_requests(prs: list[PullRequestWithScore]) -> str:
    return "\n\n".join(
        f"""PR id #{pr.pull_request.id}

Title: {pr.pull_request.title}

Test Steps: {pr.pull_request.test.strip() if pr.pull_request.test else "No test steps provided."}

Files Changed: {", ".join(pr.pull_request.files) if pr.pull_request.files else "No files listed."}

Code diff summary: {pr.pull_request.code_diff_summary if pr.pull_request.code_diff_summary else "No code diff summary provided."}

Score: {pr.score:.2f}

Explanation: {pr.pull_request.explanation.strip() if pr.pull_request.explanation else "No explanation provided."}"""
        for pr in prs
    )
