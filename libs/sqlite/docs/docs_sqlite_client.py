from libs import constants
import sqlite3
from . import docs_queries as q
from libs import constants
from typing import Optional, Set, List
from functools import wraps
import os
import json
import datetime
from models.models import Doc


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
    def upsert_doc(self, path: str, title: str, content_hash: str, embedding: str, content: str):
        assert self.connection is not None
        now = datetime.datetime.now().isoformat()

        self.connection.execute(
            q.UPSERT_DOC,
            (path, title, content_hash, embedding, content, now),
        )
        self.connection.commit()

    @require_connection
    def delete_doc(self, path: str):
        assert self.connection is not None

        self.connection.execute(q.DELETE_DOC, (path,))
        self.connection.commit()

    @require_connection
    def get_all_paths(self) -> Set[str]:
        assert self.connection is not None

        rows = self.connection.execute(q.GET_ALL_PATHS).fetchall()
        return {row["path"] for row in rows}

    @require_connection
    def get_all_docs_with_embeddings(self) -> List[Doc]:
        assert self.connection is not None

        rows = self.connection.execute(q.GET_ALL_DOCS_WITH_EMBEDDINGS).fetchall()
        return [
            Doc(
                path=row["path"],
                title=row["title"],
                content_hash=row["content_hash"],
                embedding=json.loads(row["embedding"]),
                raw_content=row["content"],
            )
            for row in rows
        ]

    @require_connection
    def get_doc_with_content_by_path(self, path: str) -> Optional[Doc]:
        assert self.connection is not None

        row = self.connection.execute(q.GET_DOC_WITH_CONTENT_BY_PATH, (path,)).fetchone()
        if not row:
            return None

        return Doc(
            path=row["path"],
            title=row["title"],
            content_hash=row["content_hash"],
            raw_content=row["content"],
        )
