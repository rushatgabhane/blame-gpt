"""Code Review Controller"""

from typing import cast

from fastapi import APIRouter, Depends, Request
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel

from libs.sqlite.core.core_sqlite_client import Database
from middlewares import auth_middleware
from services.code_review_service import generate_code_review, run_line_by_line_review

router = APIRouter()


@router.post("/api/overview", dependencies=[Depends(auth_middleware.verify_internal_auth_token)])
async def generate_repository_overview():
    """Generate repository overview and save to BLAMEGPT.md"""

    await generate_code_review()

    return {
        "message": "Repository overview generated successfully",
        "file": "BLAMEGPT.md",
    }


@router.get("/api/overview", dependencies=[Depends(auth_middleware.verify_internal_auth_token)])
async def get_repository_overview():
    """Get the generated repository overview"""

    try:
        with open("BLAMEGPT.md") as f:
            content = f.read()

        return Response(content=content, media_type="text/markdown")

    except FileNotFoundError:
        return {"error": "Repository overview not generated yet. Call /generate-overview first."}


class ReviewRequest(BaseModel):
    pr_number: int


@router.post("/api/review", dependencies=[Depends(auth_middleware.verify_internal_auth_token)])
async def review_pull_request(request: Request, data: ReviewRequest):
    """Generate line-by-line code review for a pull request"""
    
    db = cast(Database, request.app.state.db)
    
    async def generate_review():
        async for message in run_line_by_line_review(data.pr_number, db):
            yield f"#{data.pr_number}: {message}\n"
    
    return StreamingResponse(
        generate_review(),
        media_type="text/plain"
    )
