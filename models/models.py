from pydantic import BaseModel, Field
from typing import List, TypedDict, Optional


class PullRequest(BaseModel):
    id: int
    title: str
    test: str
    explaination: str
    files: List[str]
    embedding: list[float] | None = None
    code_diff_summary: str | None = None


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


class Doc(BaseModel):
    path: str
    title: str
    content_hash: str
    embedding: List[float] | None = None
    raw_content: str | None = None


class DocWithScore(BaseModel):
    doc: Doc
    score: float


class FilePatch(BaseModel):
    filename: str
    patch: str


class PullRequestIntent(BaseModel):
    intent: str
    is_bug_fix: bool = False


class Edits(BaseModel):
    before: str = Field(..., description="original text that should be replaced.")
    after: str = Field(..., description="suggested text to replace it with. Empty string means deletion.")


class DocUpdateDiff(BaseModel):
    path: str = Field(..., description="relative path of the article")
    edits: List[Edits] = Field(
        ..., description="list of edits to be applied to the article. Empty list means no edits needed."
    )


class DocEditEvaluation(BaseModel):
    should_docs_update: bool = Field(..., description="true if any user facing help articles need updates.")
    update_reason: str = Field(..., description="explanation for the decision.")
    edits_to_apply: List[DocUpdateDiff] = Field(
        ..., description="list of articles that need updates and the suggested edits to apply."
    )


class State(TypedDict):
    pull_request_id: int
    pull_request: Optional[PullRequest]
    en_patch: Optional[str]
    intent: Optional[str]
    relevant_docs: Optional[List[Doc]]
    doc_edit_suggestions: Optional[List[DocUpdateDiff]]
    should_docs_update: Optional[bool]
    update_reason: Optional[str]
    comment: Optional[str]


class CodeDiffSummary(BaseModel):
    pull_request_description: str
