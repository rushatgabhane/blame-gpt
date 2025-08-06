from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel

from middlewares import auth_middleware
from services.docs_service import run_graph

docs_router = APIRouter()


class DocPanicRequest(BaseModel):
    pull_request_id: int


@docs_router.post("/api/ohmydocs", dependencies=[Depends(auth_middleware.verify_user_auth_token)])
async def sync(request: Request, data: DocPanicRequest):
    docs_db = request.app.state.docs_db
    db = request.app.state.db

    run_graph.docs(
        pull_request_id=data.pull_request_id,
        db=db,
        docs_db=docs_db,
    )

    return Response(status_code=200)
