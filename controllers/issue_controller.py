from fastapi import APIRouter, Request
from typing import cast
from libs.sqlite.sqlite_client import Database
from services.github import issue_service

issue_router = APIRouter()


@issue_router.get("/issues")
async def get_issues(request: Request):
    db = cast(Database, request.app.state.db)
    issues = issue_service.get_all_issues(db)
    return {"issues": issues}


@issue_router.get("/issues/{issue_number}/pull_requests")
async def get_pull_requests_for_issue(request: Request, issue_number: int):
    db = cast(Database, request.app.state.db)
    pull_requests = db.get_pull_requests_for_issue(issue_number)
    return {"issue_id": issue_number, "pull_requests": pull_requests}


@issue_router.get("/issues/pull_requests")
async def get_all_pull_requests(request: Request):
    db = cast(Database, request.app.state.db)
    issue_pull_requests = db.get_all_issue_pull_requests()
    return {"issue_pull_requests": issue_pull_requests}
