"""Code Review Controller"""

from typing import cast

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from libs.sqlite.core.core_sqlite_client import Database
from middlewares import auth_middleware
from services.code_review_service import run_line_by_line_review

router = APIRouter()


class ReviewRequest(BaseModel):
    pull_request_id: int


@router.post("/api/review", dependencies=[Depends(auth_middleware.verify_user_auth_token)])
async def review_pull_request(request: Request, data: ReviewRequest):
    db = cast(Database, request.app.state.db)

    async def generate_review():
        async for message in run_line_by_line_review(data.pull_request_id, db):
            yield f"#{data.pull_request_id}: {message}\n"

    return StreamingResponse(generate_review(), media_type="text/plain")
