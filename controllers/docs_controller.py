from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel

from libs.github import get_installation_id_for_repo
from middlewares import auth_middleware
from services.docs_service import run_graph

docs_router = APIRouter()


class DocPanicRequest(BaseModel):
    pull_request_id: int
    repo_owner: str
    repo_name: str


@docs_router.post("/api/ohmydocs", dependencies=[Depends(auth_middleware.verify_user_auth_token)])
async def sync(request: Request, data: DocPanicRequest):
    docs_db = request.app.state.docs_db
    db = request.app.state.db

    installation_id = await get_installation_id_for_repo(data.repo_owner, data.repo_name)
    if not installation_id:
        return Response(status_code=400, content=f"BlameGPT app not installed on {data.repo_owner}/{data.repo_name}")

    run_graph.docs(
        pull_request_id=data.pull_request_id,
        db=db,
        docs_db=docs_db,
        installation_id=installation_id,
        repo_owner=data.repo_owner,
        repo_name=data.repo_name,
    )

    return Response(status_code=200)
