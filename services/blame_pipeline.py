import asyncio
from services.github import pull_request_service
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
from typing import List, Tuple
from libs.llm import llm
import logging
from services.github import comment_service
from libs.llm import embedding_model
from libs.helpers import cosine_similarity

logger = logging.getLogger(__name__)


async def run_blame_pipeline(issue: Issue, db: Database):
    try:
        db_issue = db.get_issue_by_id(issue.id)
        if db_issue is not None and db_issue.is_processed:
            yield f"issue already processed"
            return

        yield "fetching new pull requests"
        await asyncio.to_thread(
            pull_request_service.add_new_pull_requests_between,
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

        prs_with_scores = get_top_pull_requests_by_semantic_score(
            issue, pull_requests_without_cp, top_n=15
        )
        yield f"found {prs_with_scores} pull requests with semantic scores."
        yield f"ranked {len(prs_with_scores)} pull requests. with the highest score as {prs_with_scores[0].score if prs_with_scores else 0:.2f}"

        yield f"ranking pull requests"
        culprit_pull_requests = await asyncio.to_thread(
            find_culprit_pull_requests, issue, prs_with_scores
        )
        yield f"culprit pull requests ranked: {culprit_pull_requests}"
        if not culprit_pull_requests:
            yield f"no culprits found"
            return

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
        logger.error(f"error in blame pipeline for issue {issue.id}: {e}")
        yield f"error in blame pipeline: {e}"


def get_top_pull_requests_by_semantic_score(
    issue: Issue, pull_requests: List[PullRequest], top_n: int
) -> List[PullRequestWithScore]:
    issue_embedding = embedding_model.embed_query(f"{issue.title}\n {issue.steps}")

    pull_requests_embeddings: List[Tuple[PullRequest, float, List[float]]] = []
    for pr in pull_requests:
        pr_text = f"Title: {pr.title}\n Tests: {pr.test}\n Explaination: {pr.explaination}\n Files changed: {pr.files}"
        pr_embedding = embedding_model.embed_query(pr_text)
        pull_requests_embeddings.append((pr, 0, pr_embedding))

    scored_prs: List[PullRequestWithScore] = [
        PullRequestWithScore(
            pull_request=pr, score=cosine_similarity(issue_embedding, pr_embedding)
        )
        for pr, _, pr_embedding in pull_requests_embeddings
    ]

    scored_prs.sort(key=lambda x: x.score, reverse=True)
    top_n_culprits = scored_prs[: min(top_n, len(scored_prs))]
    return top_n_culprits if top_n_culprits else []


def find_culprit_pull_requests(
    issue: Issue, pull_requests: List[PullRequestWithScore]
) -> CulpritPullRequests | None:
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
