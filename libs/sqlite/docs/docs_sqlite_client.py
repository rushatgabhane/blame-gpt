from libs import constants
import sqlite3
from . import docs_queries as q
from libs import constants
from typing import List, Optional
from functools import wraps
import os
import json
import datetime


def require_connection(method):
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        if self.connection is None:
            raise ValueError("database connection is not initialized for docs db.")
        return method(self, *args, **kwargs)

    return wrapper


class Database:
    def __init__(self, db_path: str = constants.DOCS_DB_PATH):
        self.connection = sqlite3.connect(db_path, check_same_thread=False, timeout=15.0)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA journal_mode=WAL;")
        self.connection.execute("PRAGMA synchronous=NORMAL;")
        self.connection.execute("PRAGMA strict=ON;")
        self.connection.execute("PRAGMA foreign_keys=ON;")
        self._init_db()

    def _init_db(self):
        if self.connection is None:
            raise ValueError("database connection is not initialized for docs db.")

        self.connection.executescript(q.CREATE_TABLES)
        self.connection.commit()

    def close(self):
        if self.connection:
            self.connection.close()
            self.connection = None

    @require_connection
    def get_content_hash(self, path: str) -> Optional[str]:
        assert self.connection is not None

        row = self.connection.execute(q.GET_CONTENT_HASH, (path,)).fetchone()
        return row["content_hash"] if row else None

    @require_connection
    def upsert_doc(self, path: str, title: str, content_hash: str, embedding: str):
        assert self.connection is not None
        now = datetime.datetime.now().isoformat()

        self.connection.execute(
            q.UPSERT_DOC,
            (
                path,
                title,
                content_hash,
                embedding,
                now,
            ),
        )
        self.connection.commit()

    @require_connection
    def delete_doc(self, path: str):
        assert self.connection is not None

        self.connection.execute(q.DELETE_DOC, (path,))
        self.connection.commit()
