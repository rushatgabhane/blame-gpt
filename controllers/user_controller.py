from typing import cast

from fastapi import APIRouter, Depends, Request

from libs.sqlite.core.core_sqlite_client import Database
from middlewares import auth_middleware
from models.models import User, UserUsageLog
from services import user_service

user_router = APIRouter()


@user_router.get(
    "/api/users", response_model=list[User], dependencies=[Depends(auth_middleware.verify_internal_auth_token)]
)
async def get_users(request: Request):
    db = cast(Database, request.app.state.db)
    users = user_service.get_all_users(db)
    return users


@user_router.get(
    "/api/users/usage",
    response_model=list[UserUsageLog],
    dependencies=[Depends(auth_middleware.verify_internal_auth_token)],
)
async def get_all_user_usage(request: Request):
    db = cast(Database, request.app.state.db)
    usage_logs = user_service.get_all_usage_logs_for_all_users(db)
    return usage_logs
