from fastapi import APIRouter, HTTPException, Request
from libs import helpers
from services.github import issue_service
from services.github import pull_request_service
from services import blame_service
from libs.sqlite.sqlite_client import Database
from pydantic import BaseModel
import logging
from typing import cast
import asyncio

blame_router = APIRouter()

logger = logging.getLogger(__name__)


class BlameRequest(BaseModel):
    issue_url: str


@blame_router.post("/blame")
async def blame(request: Request, data: BlameRequest):
    db = cast(Database, request.app.state.db)
    result = helpers.parse_issue_url(data.issue_url)
    if result is None:
        raise HTTPException(
            status_code=400,
            detail="URL must be in the format: https://github.com/OWNER/REPO/issues/NUMBER",
        )

    owner, repo, issue_number = result
    if not owner or not repo or not issue_number:
        raise HTTPException(
            status_code=400,
            error="URL must be in the format: https://github.com/OWNER/REPO/issues/NUMBER",
        )

    issue = await issue_service.add_issue(issue_number, db)
    if not issue:
        raise HTTPException(
            status_code=200, detail="issue not found or not a deploy blocker"
        )

    async def run_blame_pipeline():
        pull_request_service.add_new_pull_requests(
            base="production", head="staging", issue_number=issue_number, db=db
        )

        culprits = blame_service.get_culprit_pull_requests(issue=issue, db=db)
        if culprits is None:
            logger.info(f"No culprit pull requests found for issue {issue.id}")
            return

        logger.info("Top culprit PRs for issue %s:", culprits.issue_id)
        for pr in culprits.pull_requests:
            logger.info("- PR #%s: %s, score: %d", pr.pull_request_id, pr.reason, pr.score)

    asyncio.create_task(run_blame_pipeline())

    return {"message": "blame process started successfully"}
