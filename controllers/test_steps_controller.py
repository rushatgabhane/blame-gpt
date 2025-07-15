from typing import cast

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from libs.sqlite.core.core_sqlite_client import Database
from middlewares import auth_middleware
from services.test_step import test_step_pipeline

test_steps_router = APIRouter()


class TestStepRequest(BaseModel):
    pull_request_id: int


@test_steps_router.post(
    "/api/test-steps",
    dependencies=[Depends(auth_middleware.verify_internal_auth_token)],
)
async def generate_test_steps(request: Request, d: TestStepRequest):
    db = cast(Database, request.app.state.db)

    async def stream_logs():
        async for step in test_step_pipeline.run(d.pull_request_id, db):
            yield f"#{d.pull_request_id}: {step}\n"

    return StreamingResponse(stream_logs(), media_type="text/plain")
