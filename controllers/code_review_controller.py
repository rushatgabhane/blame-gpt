"""Code Review Controller"""

from typing import cast

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from libs.sqlite.core.core_sqlite_client import Database
from middlewares import auth_middleware
from services import code_review_pipeline

router = APIRouter()


class ReviewRequest(BaseModel):
    pull_request_id: int
    repo_owner: str
    repo_name: str


@router.post("/api/review", dependencies=[Depends(auth_middleware.verify_user_auth_token)])
async def review_pull_request(request: Request, data: ReviewRequest):
    db = cast(Database, request.app.state.db)

    async def generate_review():
        async for message in code_review_pipeline.run(
            pull_request_id=data.pull_request_id, repo_owner=data.repo_owner, repo_name=data.repo_name, db=db
        ):
            yield f"#{data.pull_request_id}: {message}\n"

    return StreamingResponse(generate_review(), media_type="text/plain")
