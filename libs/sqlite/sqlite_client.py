import json
import sqlite3
from . import queries
import os
import json
from typing import Optional
from models.models import PullRequest, CulpritPullRequest, Issue
from libs import constants
from typing import List
from functools import wraps

os.makedirs(os.path.dirname(constants.CACHE_DB_PATH), exist_ok=True)


def require_connection(method):
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        if self.connection is None:
            raise ValueError("database connection is not initialized.")
        return method(self, *args, **kwargs)

    return wrapper


class Database:
    def __init__(self, db_path: str = constants.CACHE_DB_PATH):
        self.connection = sqlite3.connect(db_path, check_same_thread=False, timeout=15.0)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA journal_mode=WAL;")
        self.connection.execute("PRAGMA synchronous=NORMAL;")
        self.connection.execute("PRAGMA strict=ON;")
        self.connection.execute("PRAGMA foreign_keys=ON;")
        self._init_db()

    def _init_db(self):
        if self.connection is None:
            raise ValueError("database connection is not initialized.")

        self.connection.executescript(queries.CREATE_TABLES)
        self.connection.commit()

    def close(self):
        if self.connection:
            self.connection.close()
            self.connection = None

    @require_connection
    def get_existing_pr_ids(self) -> set[int]:
        assert self.connection is not None
        rows = self.connection.execute("SELECT id FROM pull_requests").fetchall()
        return set(row[0] for row in rows)

    @require_connection
    def add_pull_request(self, pr: PullRequest):
        assert self.connection is not None
        try:
            self.connection.execute("BEGIN;")
            self.connection.execute(
                queries.INSERT_PULL_REQUEST,
                (
                    pr.id,
                    pr.title,
                    pr.test,
                    pr.explaination,
                    json.dumps(pr.files),
                ),
            )
            self.connection.execute(
                queries.INSERT_PULL_REQUEST_EMBEDDING,
                (pr.id, json.dumps(pr.embedding)),
            )
            self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            raise e

    @require_connection
    def get_all_issues(self) -> List[Issue]:
        assert self.connection is not None
        rows = self.connection.execute(queries.GET_ALL_ISSUES).fetchall()
        if not rows:
            return []

        return [
            Issue(
                id=row[0],
                title=row[1],
                steps=row[2],
                raw_body=row[3],
                labels=json.loads(row[4]),
                is_processed=row[5],
                culprit_pull_requests=([CulpritPullRequest(**c) for c in json.loads(row[6])] if row[6] else None),
            )
            for row in rows
        ]

    @require_connection
    def add_issue(self, issue: Issue):
        assert self.connection is not None
        try:
            self.connection.execute("BEGIN;")
            self.connection.execute(
                queries.INSERT_ISSUE,
                (
                    issue.id,
                    issue.title,
                    issue.steps,
                    issue.raw_body,
                    json.dumps(issue.labels),
                ),
            )
            self.connection.execute(
                queries.INSERT_ISSUE_EMBEDDING,
                (issue.id, json.dumps(issue.embedding)),
            )
            self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            raise e

    @require_connection
    def update_issue_processed_and_result(self, issue_id: int, is_processed: bool, culprits: List[CulpritPullRequest]):
        assert self.connection is not None
        self.connection.execute(
            queries.UPDATE_ISSUE_PROCESSED_AND_CULPRITS,
            (is_processed, json.dumps([c.model_dump() for c in culprits]), issue_id),
        )
        self.connection.commit()

    @require_connection
    def get_issue_by_id(self, issue_id: int) -> Optional[Issue]:
        assert self.connection is not None
        row = self.connection.execute(queries.GET_ISSUE_BY_ID, (issue_id,)).fetchone()
        if not row:
            return None

        culprit_data = row[6]
        cullprit_pull_requests = [CulpritPullRequest(**c) for c in json.loads(culprit_data)] if culprit_data else None

        return Issue(
            id=row[0],
            title=row[1],
            steps=row[2],
            raw_body=row[3],
            labels=json.loads(row[4]),
            is_processed=row[5],
            culprit_pull_requests=cullprit_pull_requests,
        )

    @require_connection
    def get_issue_processed_status(self, issue_id: int) -> bool:
        assert self.connection is not None
        row = self.connection.execute(queries.GET_ISSUE_IS_PROCESSED, (issue_id,)).fetchone()
        if row:
            return row[0]
        return False

    @require_connection
    def add_issue_pull_request(self, issue_id: int, pull_request_id: int):
        assert self.connection is not None
        self.connection.execute(queries.INSERT_ISSUE_PULL_REQUEST, (issue_id, pull_request_id))
        self.connection.commit()

    @require_connection
    def get_pull_requests_for_issue(self, issue_id: int) -> List[PullRequest]:
        assert self.connection is not None
        rows = self.connection.execute(queries.GET_PULL_REQUESTS_BY_ISSUE_ID, (issue_id,)).fetchall()
        return [
            PullRequest(
                id=row[0],
                title=row[1],
                test=row[2],
                explaination=row[3],
                files=json.loads(row[4]),
                embedding=json.loads(row[5]) if row[5] else None,
            )
            for row in rows
        ]

    @require_connection
    def get_all_issue_pull_requests(self) -> List[tuple[int, int, float]]:
        assert self.connection is not None
        rows = self.connection.execute(queries.GET_ALL_ISSUE_PULL_REQUESTS).fetchall()
        return [(row[0], row[1], row[2]) for row in rows]

    @require_connection
    def get_pull_request_by_id_with_embedding(self, pull_request_id: int) -> Optional[PullRequest]:
        assert self.connection is not None
        row = self.connection.execute(queries.GET_PULL_REQUEST_BY_ID_WITH_EMBEDDING, (pull_request_id,)).fetchone()
        if not row:
            return None

        return PullRequest(
            id=row[0],
            title=row[1],
            test=row[2],
            explaination=row[3],
            files=json.loads(row[4]),
            embedding=json.loads(row[5]) if row[5] else None,
        )

    @require_connection
    def update_issue_pull_request_score(self, issue_id: int, pull_request_id: int, score: float):
        assert self.connection is not None
        self.connection.execute(
            queries.UPDATE_ISSUE_PULL_REQUEST_SCORE,
            (score, issue_id, pull_request_id),
        )
        self.connection.commit()

    @require_connection
    def update_issue_actual_pull_request(self, issue_id: int, pull_request_id: int):
        assert self.connection is not None
        self.connection.execute(queries.UPADTE_ISSUE_ACTUAL_PULL_REQUEST, (pull_request_id, issue_id))
        self.connection.commit()
