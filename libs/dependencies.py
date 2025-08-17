from fastapi import Request

from libs.sqlite.core.core_sqlite_client import Database


def get_database(request: Request) -> Database:
    return request.app.state.db