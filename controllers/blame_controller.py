import logging
from typing import cast

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from libs.sqlite.core.core_sqlite_client import Database
from middlewares import auth_middleware
from services import blame_pipeline

blame_router = APIRouter()

logger = logging.getLogger(__name__)


class BlameRequest(BaseModel):
    issue_id: int


@blame_router.post("/api/blame", dependencies=[Depends(auth_middleware.verify_user_auth_token)])
async def blame_manual(request: Request, data: BlameRequest):
    db = cast(Database, request.app.state.db)

    async def stream_logs():
        async for step in blame_pipeline.run(data.issue_id, db):
            yield f"#{data.issue_id}: {step}\n"

    return StreamingResponse(stream_logs(), media_type="text/plain")
