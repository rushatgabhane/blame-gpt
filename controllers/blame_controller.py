from fastapi import APIRouter, HTTPException
from libs import helpers
from services.github import issue_service
from pydantic import BaseModel

blame_router = APIRouter()


class BlameRequest(BaseModel):
    issue_url: str


@blame_router.post("/blame")
async def blame(request: BlameRequest):
    result = helpers.parse_issue_url(request.issue_url)
    if result is None:
        raise HTTPException(
            status_code=400,
            detail="URL must be in the format: https://github.com/OWNER/REPO/issues/NUMBER",
        )

    owner, repo, issue_number = result
    if not owner or not repo or not issue_number:
        raise HTTPException(
            status_code=400,
            error="URL must be in the format: https://github.com/OWNER/REPO/issues/NUMBER",
        )

    issue = await issue_service.get_issue(owner, repo, issue_number)
    if not issue:
        raise HTTPException(
            status_code=200, detail="issue not found or not a deploy blocker"
        )

    return issue
