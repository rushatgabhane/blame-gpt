from pydantic import BaseModel
from typing import List


class Issue(BaseModel):
    id: int
    title: str
    steps: str
    raw_body: str
    labels: list[str]
    is_processed: bool


class PullRequest(BaseModel):
    id: int
    title: str
    test: str
    explaination: str
    files: List[str]


class CulpritPullRequest(BaseModel):
    pull_request_id: int
    reason: str
    score: int


class CulpritPullRequests(BaseModel):
    issue_id: int
    pull_requests: List[CulpritPullRequest]
