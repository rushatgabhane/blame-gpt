from typing import cast

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from libs.sqlite.core.core_sqlite_client import Database
from middlewares import auth_middleware
from services import revert_pipeline

revert_router = APIRouter()


class RevertRequest(BaseModel):
    pull_request_id: int


@revert_router.post("/api/revert", dependencies=[Depends(auth_middleware.verify_internal_auth_token)])
async def revert(request: Request, data: RevertRequest):
    db = cast(Database, request.app.state.db)

    async def stream_logs():
        async for step in revert_pipeline.run(data.pull_request_id, db):
            yield f"#{data.pull_request_id}: {step}\n"

    return StreamingResponse(stream_logs(), media_type="text/plain")
