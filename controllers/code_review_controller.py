"""Code Review Controller"""

from typing import cast

from fastapi import APIRouter, Depends, Request
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel

from libs.github import get_github_client, get_installation_id_for_repo
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

    installation_id = await get_installation_id_for_repo(data.repo_owner, data.repo_name)
    if not installation_id:
        return Response(status_code=400, content=f"BlameGPT app not installed on {data.repo_owner}/{data.repo_name}")

    gh_client = get_github_client(installation_id)
    repo_client = gh_client.get_repo(f"{data.repo_owner}/{data.repo_name}")

    async def generate_review():
        async for message in code_review_pipeline.run(
            pull_request_id=data.pull_request_id,
            repo_owner=data.repo_owner,
            repo_name=data.repo_name,
            db=db,
            repo_client=repo_client,
            installation_id=installation_id,
        ):
            yield f"#{data.pull_request_id}: {message}\n"

    return StreamingResponse(generate_review(), media_type="text/plain")
