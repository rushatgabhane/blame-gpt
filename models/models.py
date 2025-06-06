from pydantic import BaseModel
from typing import List


class PullRequest(BaseModel):
    id: int
    title: str
    test: str
    explaination: str
    files: List[str]
    embedding: list[float] | None = None


class CulpritPullRequest(BaseModel):
    pull_request_id: int
    reason: str


class CulpritPullRequests(BaseModel):
    issue_id: int
    pull_requests: List[CulpritPullRequest]


class Issue(BaseModel):
    id: int
    title: str
    steps: str
    raw_body: str
    labels: List[str]
    is_processed: bool = False
    culprit_pull_requests: List[CulpritPullRequest] | None = None
    embedding: list[float] | None = None
    actual_pull_request_id: int | None = None


class PullRequestWithScore(BaseModel):
    pull_request: PullRequest
    score: float
