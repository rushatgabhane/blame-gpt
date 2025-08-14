from typing import TypedDict

from github import Github
from github.Repository import Repository
from pydantic import BaseModel, Field

from models.enums import CodeReviewCommentType, CommandName


class PullRequest(BaseModel):
    id: int
    title: str
    test: str
    explanation: str
    files: list[str]
    embedding: list[float] | None = None
    code_diff_summary: str | None = None
    generated_test_steps: str | None = None
    code_diff: str | None = None
    linked_issue_ids: list[int] | None = None
    commit_sha: str | None = None


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
    usage_log_id: int | None
    installation_id: int | None
    gh_client: Github | None
    repo_client: Repository | None


class CodeDiffSummary(BaseModel):
    pull_request_description: str


class GeneratedTestSteps(BaseModel):
    title: str = Field(
        ..., description="a really short title for what to verify. For example: you can remove a workspace member"
    )
    precondition: str | None = Field(
        ...,
        description="a precondition is usually setup like workspace settings that you need to enable.",
    )
    steps: str = Field(
        ...,
        description="a numbered list of steps to verify the PR. For example: 1. Login to Expensify App. 2. Go to workspace settings > Members. 3. Click on the member with VISA card. 4. Click on the card. 5. Click QuickBooks Online credit card export. 6. Verify that the export is successful and the VISA card transactions are exported to QBO.",
    )


class GeneratedTestStepsList(BaseModel):
    test: list[GeneratedTestSteps]


class CommandClassification(BaseModel):
    command_name: CommandName


class User(BaseModel):
    id: int
    name: str
    username: str
    email: str | None = None
    avatar_url: str
    is_active: bool


class UsageLog(BaseModel):
    id: int
    user_id: int
    command_name: CommandName
    comment_url: str
    output: str
    issue_or_pull_request_url: str
    created_at: str
    comment_text: str | None = None


class CodeReviewComment(BaseModel):
    file: str = Field(..., description="The file path where the comment applies")
    line: int = Field(
        ...,
        description="The relevant line number where the comment ends (inclusive). Should correspond to the line number prefix shown in the diff.",
    )
    start_line: int | None = Field(
        default=None,
        description="The relevant line number where the comment starts (inclusive). Should correspond to the line number prefix shown in the diff. Leave empty for single-line comments",
    )
    content: str = Field(
        ...,
        description="The review comment content. Don't add label here. Be concise. Split in new paragraphs if needed.",
    )
    label: CodeReviewCommentType = Field(..., description="Conventional comment label")


class PRFileDiff(BaseModel):
    filename: str = Field(description="Name of the file")
    status: str = Field(description="Status of the file: 'added', 'modified', 'deleted'")
    additions: int = Field(description="Number of lines added")
    deletions: int = Field(description="Number of lines deleted")
    patch: str | None = Field(description="The actual diff patch content")


class LineByLineCodeReview(BaseModel):
    pr_number: int = Field(..., description="Pull request number")
    comments: list[CodeReviewComment] = Field(default=[], description="List of review comments")
    code_overview: str = Field(
        ..., description="Brief description of the pull request in markdown format with ### headers and bullet points."
    )
    files_reviewed: list[str] | None = Field(default=None, description="List of files that were reviewed")


class LLMCall(BaseModel):
    id: int
    usage_log_id: int
    llm_model: str
    tokens_used: int
    cost_usd_thousandths: int  # Stores cost in 0.001 USD units (1 = 0.001 USD)
    created_at: str


class UserUsageLog(BaseModel):
    user: User
    usage_log: UsageLog
    llm_calls: list[LLMCall] = []


class TestSuite(BaseModel):
    id: int
    case_id: int
    title: str
    steps: str
    hash: str
    embedding: list[float] | None = None
