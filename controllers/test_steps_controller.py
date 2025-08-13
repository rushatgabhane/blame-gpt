from typing import cast

from fastapi import APIRouter, Depends, Request
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel

from libs.github import get_github_client, get_installation_id_for_repo
from libs.sqlite.core.core_sqlite_client import Database
from middlewares import auth_middleware
from services.test_step import test_step_pipeline

test_steps_router = APIRouter()


class TestStepRequest(BaseModel):
    pull_request_id: int
    repo_owner: str
    repo_name: str


@test_steps_router.post(
    "/api/test-steps",
    dependencies=[Depends(auth_middleware.verify_internal_auth_token)],
)
async def generate_test_steps(request: Request, d: TestStepRequest):
    db = cast(Database, request.app.state.db)

    installation_id = await get_installation_id_for_repo(d.repo_owner, d.repo_name)
    if not installation_id:
        return Response(status_code=400, content=f"BlameGPT app not installed on {d.repo_owner}/{d.repo_name}")

    gh_client = get_github_client(installation_id)
    repo_client = gh_client.get_repo(f"{d.repo_owner}/{d.repo_name}")

    async def stream_logs():
        async for step in test_step_pipeline.run(
            pull_request_id=d.pull_request_id,
            db=db,
            repo_client=repo_client,
        ):
            yield f"#{d.pull_request_id}: {step}\n"

    return StreamingResponse(stream_logs(), media_type="text/plain")
