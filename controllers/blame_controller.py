from fastapi import APIRouter, Request, Header, Response, Depends
from fastapi.responses import StreamingResponse
from libs import helpers
from middlewares import auth_middleware
from services import blame_pipeline
from libs.sqlite.sqlite_client import Database
from pydantic import BaseModel
import logging
from typing import cast
import asyncio
import os
import json
from libs import constants

blame_router = APIRouter()

logger = logging.getLogger(__name__)


class ManualBlameRequest(BaseModel):
    issue_id: int


# This is a webhook endpoint that listens for GitHub events.
@blame_router.post("/api/webhook")
async def blame(request: Request, x_hub_signature_256: str = Header(None)):
    body = await request.body()
    if not helpers.is_valid_signature(x_hub_signature_256, os.getenv("GITHUB_WEBHOOK_SECRET") or "", body):
        return Response(status_code=403, content="Invalid signature")

    payload = json.loads(body)
    if payload.get("action") != "labeled":
        return Response(status_code=200, content="action is not 'labeled'")

    if payload.get("label").get("name") != constants.LABELS["DeployBlockerCash"]:
        return Response(status_code=200, content="label is not 'DeployBlockerCash'")

    repository_name = payload.get("repository").get("name")
    repository_owner = payload.get("repository").get("owner").get("login")

    if repository_name != constants.REPO_NAME or repository_owner != constants.REPO_OWNER:
        return Response(
            status_code=200,
            content=f"this repository is not supported",
        )

    issue = payload.get("issue")
    issue_number = issue.get("number")
    db = cast(Database, request.app.state.db)

    asyncio.create_task(run_and_log_blame_pipeline(issue_number, db))
    return Response(status_code=200, content=f"blame process started for #{issue_number}")


@blame_router.post("/api/blame", dependencies=[Depends(auth_middleware.verify_user_auth_token)])
async def blame_manual(request: Request, data: ManualBlameRequest):
    db = cast(Database, request.app.state.db)

    async def stream_logs():
        async for step in blame_pipeline.run(data.issue_id, db):
            yield f"#{data.issue_id}: {step}\n"

    return StreamingResponse(stream_logs(), media_type="text/plain")


async def run_and_log_blame_pipeline(issue_id: int, db: Database):
    async for step in blame_pipeline.run(issue_id, db):
        logger.info(f"{issue_id}: {step}")
