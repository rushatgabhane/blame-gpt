from fastapi import APIRouter, HTTPException, Request
from libs import helpers
from services.github import issue_service
from models.models import Issue
from services import blame_pipeline
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
            detail="URL must be in the format: https://github.com/OWNER/REPO/issues/NUMBER",
        )

    issue = await issue_service.add_issue(issue_number, db)
    if not issue:
        raise HTTPException(
            status_code=200, detail="issue not found or not a deploy blocker"
        )

    asyncio.create_task(run_and_log_blame_pipeline(issue, db))

    return {"message": "blame process started successfully"}


async def run_and_log_blame_pipeline(issue: Issue, db: Database):
    async for step in blame_pipeline.run_blame_pipeline(issue, db):
        logger.info(f"issue {issue.id}: {step}")
