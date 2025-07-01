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
import sqlite_vec
import numpy as np


def _embedding_to_vector(embedding: List[float]) -> bytes:
    """Convert embedding list to vector bytes for sqlite-vec"""
    return np.array(embedding, dtype=np.float32).tobytes()


def _vector_to_embedding(vector_bytes: bytes) -> List[float]:
    """Convert vector bytes from sqlite-vec to embedding list"""
    return np.frombuffer(vector_bytes, dtype=np.float32).tolist()


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
        
        # Load sqlite-vec extension
        self.connection.enable_load_extension(True)
        sqlite_vec.load(self.connection)
        
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
    def upsert_doc(self, path: str, title: str, content_hash: str, embedding: List[float], content: str):
        assert self.connection is not None
        now = datetime.datetime.now().isoformat()

        try:
            self.connection.execute("BEGIN;")
            self.connection.execute(
                q.UPSERT_DOC,
                (path, title, content_hash, content, now),
            )
            self.connection.execute(
                q.UPSERT_DOC_EMBEDDING,
                (path, _embedding_to_vector(embedding)),
            )
            self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            raise e

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
                embedding=_vector_to_embedding(row["embedding"]) if row["embedding"] else None,
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

    @require_connection  
    def get_docs_by_similarity(self, query_embedding: List[float], limit: int = 100) -> List[tuple[str, float]]:
        """Get documents ordered by vector similarity to the query embedding.
        Returns list of (doc_path, distance) tuples ordered by similarity."""
        assert self.connection is not None
        
        query_vector = _embedding_to_vector(query_embedding)
        
        query = """
        SELECT path, distance 
        FROM doc_embeddings 
        WHERE embedding MATCH ? 
        ORDER BY distance 
        LIMIT ?
        """
        
        rows = self.connection.execute(query, (query_vector, limit)).fetchall()
        return [(row[0], row[1]) for row in rows]
