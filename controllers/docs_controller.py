from fastapi import APIRouter, Depends, Request
from services.docs.sync_docs import sync_docs

from middlewares import auth_middleware

docs_router = APIRouter()


@docs_router.post("/api/docs", dependencies=[Depends(auth_middleware.verify_internal_auth_token)])
async def sync(request: Request):
    docs_db = request.app.state.docs_db
