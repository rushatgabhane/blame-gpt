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


class CodeDiffSummary(BaseModel):
    pull_request_description: str


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
    comments: list[CodeReviewComment] = Field(default_factory=list, description="List of review comments")
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
