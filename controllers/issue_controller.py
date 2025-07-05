from typing import cast

from fastapi import APIRouter, Depends, Request

from libs.sqlite.core.core_sqlite_client import Database
from middlewares import auth_middleware
from services.github import issue_service

issue_router = APIRouter()


@issue_router.get("/api/issues", dependencies=[Depends(auth_middleware.verify_internal_auth_token)])
async def get_issues(request: Request):
    db = cast(Database, request.app.state.db)
    issues = issue_service.get_all_issues(db)
    return {"issues": issues}


@issue_router.get(
    "/api/issues/{issue_number}/pull-requests",
    dependencies=[Depends(auth_middleware.verify_internal_auth_token)],
)
async def get_pull_requests_for_issue(request: Request, issue_number: int):
    db = cast(Database, request.app.state.db)
    pull_requests = db.get_pull_requests_for_issue(issue_number)
    return {"issue_id": issue_number, "pull_requests": pull_requests}


@issue_router.get(
    "/api/issues/pull-requests",
    dependencies=[Depends(auth_middleware.verify_internal_auth_token)],
)
async def get_all_pull_requests(request: Request):
    db = cast(Database, request.app.state.db)
    issue_pull_requests = db.get_all_issue_pull_requests()
    return {"issue_pull_requests": issue_pull_requests}


@issue_router.get(
    "/api/pull-requests/{pull_request_id}",
    dependencies=[Depends(auth_middleware.verify_internal_auth_token)],
)
async def get_pull_request_by_id_with_embedding(request: Request, pull_request_id: int):
    db = cast(Database, request.app.state.db)
    pull_request = db.get_pull_request_by_id_with_embedding(pull_request_id)
    return {"pull_request": pull_request}
