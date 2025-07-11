from typing import TypedDict

from pydantic import BaseModel, Field

from models.enums import CommandName


class PullRequest(BaseModel):
    id: int
    title: str
    test: str
    explaination: str
    files: list[str]
    embedding: list[float] | None = None
    code_diff_summary: str | None = None
    test_steps: str | None = None
    code_diff: str | None = None


class CulpritPullRequest(BaseModel):
    pull_request_id: int
    reason: str


class CulpritPullRequests(BaseModel):
    issue_id: int
    pull_requests: list[CulpritPullRequest]


class Issue(BaseModel):
    id: int
    title: str
    steps: str
    raw_body: str
    labels: list[str]
    is_processed: bool = False
    culprit_pull_requests: list[CulpritPullRequest] | None = None
    embedding: list[float] | None = None
    actual_pull_request_id: int | None = None


class PullRequestWithScore(BaseModel):
    pull_request: PullRequest
    score: float


class Doc(BaseModel):
    path: str
    title: str
    content_hash: str
    embedding: list[float] | None = None
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
    edits: list[Edits] = Field(
        ..., description="list of edits to be applied to the article. Empty list means no edits needed."
    )


class DocEditEvaluation(BaseModel):
    should_docs_update: bool = Field(..., description="true if any user facing help articles need updates.")
    update_reason: str = Field(..., description="explanation for the decision.")
    edits_to_apply: list[DocUpdateDiff] = Field(
        ..., description="list of articles that need updates and the suggested edits to apply."
    )


class State(TypedDict):
    pull_request_id: int
    pull_request: PullRequest | None
    en_patch: str | None
    intent: str | None
    relevant_docs: list[Doc] | None
    doc_edit_suggestions: list[DocUpdateDiff] | None
    should_docs_update: bool | None
    update_reason: str | None
    comment: str | None


class CodeDiffSummary(BaseModel):
    pull_request_description: str


class TestStepsGeneration(BaseModel):
    steps: str


class CommandClassification(BaseModel):
    command_name: CommandName


class User(BaseModel):
    id: int
    name: str
    username: str
    email: str
    avatar_url: str
    is_active: bool


class UserUsageLog(BaseModel):
    user: User
    id: int
    command_name: CommandName
    comment_url: str
    output: str
    issue_or_pull_request_url: str
    created_at: str

class UsageLog(BaseModel):
    id: int
    user_id: int
    command_name: CommandName
    comment_url: str
    output: str
    issue_or_pull_request_url: str
    created_at: str