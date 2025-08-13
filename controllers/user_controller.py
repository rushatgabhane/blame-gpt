from typing import cast

from fastapi import APIRouter, Depends, Request

from libs.sqlite.core.core_sqlite_client import Database
from middlewares import auth_middleware
from services.user_service import get_all_usage_logs_for_all_users, get_all_users

user_router = APIRouter()


@user_router.get("/api/users", dependencies=[Depends(auth_middleware.verify_internal_auth_token)])
async def get_users(request: Request):
    db = cast(Database, request.app.state.db)

    users = get_all_users(core_db=db)
    return {"users": users}


@user_router.get("/api/users/usage", dependencies=[Depends(auth_middleware.verify_internal_auth_token)])
async def get_users_usage(request: Request):
    db = cast(Database, request.app.state.db)
    usage_logs = get_all_usage_logs_for_all_users(core_db=db)
    return {"usage_logs": usage_logs}
