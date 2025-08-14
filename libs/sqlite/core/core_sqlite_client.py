import json
import os
import pickle
import sqlite3
from functools import wraps
from pathlib import Path

from yoyo import get_backend, read_migrations

from libs.sqlite.core import core_queries
from models.enums import CommandName
from models.models import CulpritPullRequest, Issue, LLMCall, PullRequest, UsageLog, User, UserUsageLog


def require_connection(method):
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        if self.connection is None:
            raise ValueError("database connection is not initialized.")
        return method(self, *args, **kwargs)

    return wrapper


class Database:
    def __init__(self, db_path: str):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        migrations_directory: Path = Path(__file__).parent / "migrations"
        backend = get_backend(f"sqlite:///{db_path}")
        migrations = read_migrations(str(migrations_directory))
        backend.apply_migrations(backend.to_apply(migrations))

        self.connection = sqlite3.connect(db_path, check_same_thread=False, timeout=15.0)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA journal_mode=WAL;")
        self.connection.execute("PRAGMA synchronous=NORMAL;")
        self.connection.execute("PRAGMA strict=ON;")
        self.connection.execute("PRAGMA foreign_keys=ON;")

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
            self.connection.execute(
                core_queries.INSERT_PULL_REQUEST,
                (
                    pr.id,
                    pr.title,
                    pr.test,
                    pr.explanation,
                    json.dumps(pr.files),
                    pr.code_diff_summary if pr.code_diff_summary else None,
                    json.dumps(pr.linked_issue_ids) if pr.linked_issue_ids else None,
                ),
            )
            self.connection.execute(
                core_queries.INSERT_PULL_REQUEST_EMBEDDING,
                (pr.id, pickle.dumps(pr.embedding)),
            )
            self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            raise e

    # Does not return embeddings
    @require_connection
    def get_all_issues(self) -> list[Issue]:
        assert self.connection is not None
        rows = self.connection.execute(core_queries.GET_ALL_ISSUES).fetchall()
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
            self.connection.execute(
                core_queries.INSERT_ISSUE,
                (
                    issue.id,
                    issue.title,
                    issue.steps,
                    issue.raw_body,
                    json.dumps(issue.labels),
                ),
            )
            self.connection.execute(
                core_queries.INSERT_ISSUE_EMBEDDING,
                (issue.id, pickle.dumps(issue.embedding)),
            )
            self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            raise e

    @require_connection
    def update_issue_processed_and_result(self, issue_id: int, is_processed: bool, culprits: list[CulpritPullRequest]):
        assert self.connection is not None
        self.connection.execute(
            core_queries.UPDATE_ISSUE_PROCESSED_AND_CULPRITS,
            (is_processed, json.dumps([c.model_dump() for c in culprits]), issue_id),
        )
        self.connection.commit()

    @require_connection
    def get_issue_by_id(self, issue_id: int) -> Issue | None:
        assert self.connection is not None
        row = self.connection.execute(core_queries.GET_ISSUE_BY_ID, (issue_id,)).fetchone()
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
            actual_pull_request_id=row[7] if row[7] else None,
        )

    @require_connection
    def get_issue_processed_status(self, issue_id: int) -> bool:
        assert self.connection is not None
        row = self.connection.execute(core_queries.GET_ISSUE_IS_PROCESSED, (issue_id,)).fetchone()
        if row:
            return row[0]
        return False

    @require_connection
    def add_issue_pull_request(self, issue_id: int, pull_request_id: int):
        assert self.connection is not None
        self.connection.execute(core_queries.INSERT_ISSUE_PULL_REQUEST, (issue_id, pull_request_id))
        self.connection.commit()

    @require_connection
    def get_pull_requests_for_issue(self, issue_id: int) -> list[PullRequest]:
        assert self.connection is not None
        rows = self.connection.execute(core_queries.GET_PULL_REQUESTS_BY_ISSUE_ID, (issue_id,)).fetchall()
        return [
            PullRequest(
                id=row[0],
                title=row[1],
                test=row[2],
                explanation=row[3],
                files=json.loads(row[4]),
                code_diff_summary=row[5] if row[5] else None,
                embedding=pickle.loads(row[6]) if row[6] else None,
            )
            for row in rows
        ]

    @require_connection
    def get_all_issue_pull_requests(self) -> list[tuple[int, int, float]]:
        assert self.connection is not None
        rows = self.connection.execute(core_queries.GET_ALL_ISSUE_PULL_REQUESTS).fetchall()
        return [(row[0], row[1], row[2]) for row in rows]

    @require_connection
    def get_pull_request_by_id_with_embedding(self, pull_request_id: int) -> PullRequest | None:
        assert self.connection is not None
        row = self.connection.execute(core_queries.GET_PULL_REQUEST_BY_ID_WITH_EMBEDDING, (pull_request_id,)).fetchone()
        if not row:
            return None

        return PullRequest(
            id=row[0],
            title=row[1],
            test=row[2],
            explanation=row[3],
            files=json.loads(row[4]),
            code_diff_summary=row[5] if row[5] else None,
            linked_issue_ids=json.loads(row[6]) if row[6] else [],
            embedding=pickle.loads(row[7]) if row[7] else None,
        )

    @require_connection
    def update_issue_pull_request_score(self, issue_id: int, pull_request_id: int, score: float):
        assert self.connection is not None
        self.connection.execute(
            core_queries.UPDATE_ISSUE_PULL_REQUEST_SCORE,
            (score, issue_id, pull_request_id),
        )
        self.connection.commit()

    @require_connection
    def update_issue_actual_pull_request(self, issue_id: int, pull_request_id: int):
        assert self.connection is not None
        self.connection.execute(core_queries.UPADTE_ISSUE_ACTUAL_PULL_REQUEST, (pull_request_id, issue_id))
        self.connection.commit()

    @require_connection
    def add_user(self, username: str, email: str, name: str, avatar_url: str) -> int | None:
        assert self.connection is not None
        try:
            row = self.connection.execute(
                core_queries.ADD_USER,
                (username, email, name, avatar_url),
            ).fetchone()
            self.connection.commit()
            return row[0] if row else None
        except Exception as e:
            self.connection.rollback()
            raise e

    @require_connection
    def get_user_by_username(self, username: str) -> User | None:
        assert self.connection is not None
        row = self.connection.execute(core_queries.GET_USER_BY_USERNAME, (username,)).fetchone()
        if not row:
            return None

        return User(
            id=row[0],
            username=row[1],
            email=row[2],
            name=row[3],
            avatar_url=row[4],
            is_active=row[5],
        )

    @require_connection
    def get_user_id_by_username(self, username: str) -> int | None:
        assert self.connection is not None
        row = self.connection.execute(core_queries.GET_USER_ID_BY_USERNAME, (username,)).fetchone()
        if not row:
            return None
        return row[0]

    @require_connection
    def add_usage_log(
        self,
        user_id: int,
        command_name: CommandName,
        comment_url: str,
        output: str,
        issue_or_pull_request_url: str | None = None,
        comment_text: str | None = None,
    ) -> int | None:
        assert self.connection is not None
        cursor = self.connection.execute(
            core_queries.ADD_USAGE_LOG,
            (user_id, command_name.value, comment_url, output, issue_or_pull_request_url, comment_text),
        )
        self.connection.commit()
        return cursor.lastrowid

    @require_connection
    def get_all_users(self) -> list[User]:
        assert self.connection is not None
        rows = self.connection.execute(core_queries.GET_ALL_USERS).fetchall()
        return [
            User(
                id=row[0],
                username=row[1],
                email=row[2],
                name=row[3],
                avatar_url=row[4],
                is_active=row[5],
            )
            for row in rows
        ]

    @require_connection
    def get_all_usage_logs_for_all_users(self) -> list[UserUsageLog]:
        assert self.connection is not None
        rows = self.connection.execute(core_queries.GET_ALL_USAGE_LOGS_FOR_ALL_USERS).fetchall()

        # Group by usage_log_id to collect LLM calls
        usage_logs = {}
        for row in rows:
            usage_log_id = row[0]

            if usage_log_id not in usage_logs:
                usage_logs[usage_log_id] = UserUsageLog(
                    usage_log=UsageLog(
                        id=row[0],
                        user_id=row[7],
                        command_name=CommandName(row[1]),
                        comment_url=row[2],
                        output=row[3],
                        issue_or_pull_request_url=row[4],
                        created_at=row[5],
                        comment_text=row[6] if row[6] else None,
                    ),
                    user=User(
                        id=row[7],
                        username=row[8],
                        email=row[9],
                        name=row[10],
                        avatar_url=row[11],
                        is_active=row[12],
                    ),
                    llm_calls=[],
                )

            if row[13] is not None:
                usage_logs[usage_log_id].llm_calls.append(
                    LLMCall(
                        id=row[13],
                        usage_log_id=row[14],
                        llm_model=row[15],
                        tokens_used=row[16],
                        cost_usd_thousandths=row[17],
                        created_at=row[18],
                    )
                )

        return list(usage_logs.values())

    @require_connection
    def get_usage_logs_by_user_id(self, user_id: int) -> list[UsageLog]:
        assert self.connection is not None
        rows = self.connection.execute(core_queries.GET_USAGE_LOGS_BY_USER_ID, (user_id,)).fetchall()
        return [
            UsageLog(
                id=row[0],
                user_id=row[1],
                command_name=CommandName(row[2]),
                comment_url=row[3],
                output=row[4],
                issue_or_pull_request_url=row[5],
                created_at=row[6],
            )
            for row in rows
        ]

    @require_connection
    def add_llm_call(self, usage_log_id: int, llm_model: str, tokens_used: int, cost_usd_thousandths: int):
        assert self.connection is not None
        self.connection.execute(
            core_queries.ADD_LLM_CALL,
            (usage_log_id, llm_model, tokens_used, cost_usd_thousandths),
        )
        self.connection.commit()

    @require_connection
    def get_pull_request_review_sha(self, pull_request_id: int, repo_id: int) -> str | None:
        assert self.connection is not None
        row = self.connection.execute(
            core_queries.GET_PULL_REQUEST_REVIEW_SHA,
            (pull_request_id, repo_id),
        ).fetchone()
        return row[0] if row else None

    @require_connection
    def update_pull_request_review(self, pull_request_id: int, repo_id: int, commit_sha: str):
        assert self.connection is not None
        self.connection.execute(
            core_queries.INSERT_OR_UPDATE_PULL_REQUEST_REVIEW,
            (pull_request_id, repo_id, commit_sha),
        )
        self.connection.commit()
