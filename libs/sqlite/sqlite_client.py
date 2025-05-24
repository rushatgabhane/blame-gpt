import json
import sqlite3
from . import queries
import os
import json
from typing import Optional
from models.models import PullRequest
from models.models import Issue
from libs import constants
from typing import List

os.makedirs(os.path.dirname(constants.DB_PATH), exist_ok=True)


class Database:
    def __init__(self, db_path: str = constants.DB_PATH):
        self.connection = sqlite3.connect(db_path, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self):
        self.connection.executescript(queries.CREATE_TABLES)
        self.connection.commit()

    def close(self):
        if self.connection:
            self.connection.close()
            self.connection = None

    def get_existing_pr_ids(self) -> set[int]:
        rows = self.connection.execute("SELECT id FROM pull_requests").fetchall()
        return set(row[0] for row in rows)

    def get_pr_by_id(self, pr_id: int) -> Optional[PullRequest]:
        row = self.connection.execute(queries.SELECT_PR_BY_ID, (pr_id,)).fetchone()
        if not row:
            return None
        return PullRequest(
            id=row[0],
            title=row[1],
            test=row[2],
            explaination=row[3],
            files=json.loads(row[4]),
        )

    def add_pull_request(self, pr: PullRequest):
        self.connection.execute(
            queries.INSERT_PULL_REQUEST,
            (pr.id, pr.title, pr.test, pr.explaination, json.dumps(pr.files)),
        )
        self.connection.commit()

    def get_all_issues(self) -> List[Issue]:
        rows = self.connection.execute(queries.GET_ALL_ISSUES).fetchall()
        return [
            Issue(
                id=row[0],
                title=row[1],
                steps=row[2],
                raw_body=row[3],
                labels=json.loads(row[4]),
            )
            for row in rows
        ]

    def add_issue(self, issue: Issue):
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
        self.connection.commit()

    def add_issue_pull_request(self, issue_id: int, pull_request_id: int):
        self.connection.execute(
            queries.INSERT_ISSUE_PULL_REQUEST, (issue_id, pull_request_id)
        )
        self.connection.commit()

    def get_pull_requests_for_issue(self, issue_id: int) -> List[PullRequest]:
        rows = self.connection.execute(
            queries.GET_PULL_REQUESTS_BY_ISSUE_ID, (issue_id,)
        ).fetchall()
        return [
            PullRequest(
                id=row[0],
                title=row[1],
                test=row[2],
                explaination=row[3],
                files=json.loads(row[4]),
            )
            for row in rows
        ]

    def get_all_issue_pull_requests(self) -> List[tuple[int, int]]:
        rows = self.connection.execute(queries.GET_ALL_ISSUE_PULL_REQUESTS).fetchall()
        return [(row[0], row[1]) for row in rows]
