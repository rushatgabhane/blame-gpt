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
from libs.llm import embedding_model
from libs.helpers import cosine_similarity

logger = logging.getLogger(__name__)


async def run(issue_id: int, db: Database):
    try:
        is_processed = db.get_issue_processed_status(issue_id)
        if is_processed:
            yield f"issue already processed"
            return

        issue = await issue_service.add_issue(issue_id, db)
        yield f"issue added to database"

        yield "fetching new pull requests"
        await asyncio.to_thread(
            pull_request_service.add_new_pull_requests_between,
            base="production",
            head="staging",
            issue_id=issue_id,
            db=db,
        )

        pull_requests = db.get_pull_requests_for_issue(issue_id)
        if not pull_requests or len(pull_requests) == 0:
            yield f"no pull requests found"
            return

        yield f"found {len(pull_requests)} pull requests on staging but not on production."

        pull_requests_without_cp = [
            pr for pr in pull_requests if "cp staging" not in pr.title.lower()
        ]
        yield f"found {len(pull_requests_without_cp)} pull requests without 'cp staging'."

        prs_with_scores = add_pull_request_semantic_score(
            issue, pull_requests_without_cp, db=db
        )
        if not prs_with_scores or len(prs_with_scores) == 0:
            yield f"no pull requests with semantic scores found"
            return

        yield f"found {len(prs_with_scores)} pull requests with semantic scores."

        yield f"ranking pull requests"
        culprit_pull_requests = await asyncio.to_thread(
            find_culprit_pull_requests, issue, prs_with_scores
        )
        if not culprit_pull_requests or not culprit_pull_requests.pull_requests:
            yield f"no culprits found"
            return

        yield f"culprit pull requests ranked: {len(culprit_pull_requests.pull_requests)}"

        yield f"found {len(culprit_pull_requests.pull_requests)} culprit pull requests."
        comment = await comment_service.add_comment(
            issue_number=issue.id, culprit_pull_requests=culprit_pull_requests
        )
        yield f"comment {comment}"

        db.update_issue_processed_and_result(
            issue.id, True, culprit_pull_requests.pull_requests
        )
        yield f"blame pipeline completed"
    except Exception as e:
        logger.error(f"error in blame pipeline for issue {issue_id}: {e}")
        yield f"error in blame pipeline: {e}"


def add_pull_request_semantic_score(
    issue: Issue, pull_requests: List[PullRequest], db: Database
) -> List[PullRequestWithScore]:
    scored_prs: List[PullRequestWithScore] = [
        PullRequestWithScore(
            pull_request=pr, score=cosine_similarity(issue.embedding, pr.embedding)
        )
        for pr in pull_requests
    ]

    for i, pr in enumerate(scored_prs):
        db.update_issue_pull_request_score(
            issue_id=issue.id, pull_request_id=pr.pull_request.id, score=pr.score
        )

    return scored_prs if scored_prs else []


def find_culprit_pull_requests(
    issue: Issue, pull_requests: List[PullRequestWithScore]
) -> CulpritPullRequests | None:
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
