import asyncio
from typing import cast

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from libs.sqlite.core.core_sqlite_client import Database
from middlewares import auth_middleware
from services.test_generation.generate_test_steps import generate_test_steps_for_pull_request

test_steps_router = APIRouter()


class TestStepRequest(BaseModel):
    pull_request_id: int


@test_steps_router.post(
    "/api/test-steps",
    dependencies=[Depends(auth_middleware.verify_internal_auth_token)],
)
async def generate_test_steps(request: Request, d: TestStepRequest):
    db = cast(Database, request.app.state.db)

    # Run in thread pool to avoid blocking the event loop
    def sync_wrapper():
        return asyncio.run(generate_test_steps_for_pull_request(d.pull_request_id, db))

    t = await asyncio.to_thread(sync_wrapper)
    return {"test_steps": t}
