import logging
from typing import cast

from fastapi import APIRouter, Depends, Request
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel

from libs.github import get_github_client, get_installation_id_for_repo
from libs.sqlite.docs.docs_sqlite_client import Database
from middlewares import auth_middleware
from services import revert_pipeline

revert_router = APIRouter()
logger = logging.getLogger(__name__)


class RevertRequest(BaseModel):
    pull_request_id: int
    repo_owner: str
    repo_name: str


@revert_router.post("/api/revert", dependencies=[Depends(auth_middleware.verify_internal_auth_token)])
async def revert(request: Request, data: RevertRequest):
    db = cast(Database, request.app.state.docs_db)

    installation_id = await get_installation_id_for_repo(data.repo_owner, data.repo_name)
    if not installation_id:
        return Response(status_code=400, content=f"BlameGPT app not installed on {data.repo_owner}/{data.repo_name}")

    gh_client = get_github_client(installation_id)
    repo_client = gh_client.get_repo(f"{data.repo_owner}/{data.repo_name}")

    async def generate_revert():
        async for message in revert_pipeline.run(data.pull_request_id, repo_client, db):
            yield f"#{data.pull_request_id}: {message}\n"

    return StreamingResponse(generate_revert(), media_type="text/plain")
