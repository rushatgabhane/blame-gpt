from typing import Any, TypedDict

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
    generated_test_steps: str | None = None
    code_diff: str | None = None
    linked_issue_ids: list[int] | None = None


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
    file: str = Field(description="The file path where the comment applies")
    start_line: int = Field(description="The starting line number for the comment")
    end_line: int = Field(description="The ending line number for the comment")
    content: str = Field(description="The review comment content")
    label: str = Field(description="Conventional comment label")
    category: str = Field(description="Comment category: 'bug', 'security', 'performance', 'quality', 'test'")


class PRDiff(BaseModel):
    filename: str = Field(description="Name of the file")
    status: str = Field(description="Status of the file: 'added', 'modified', 'deleted'")
    additions: int = Field(description="Number of lines added")
    deletions: int = Field(description="Number of lines deleted")
    patch: str | None = Field(description="The actual diff patch content")


class LineByLineCodeReview(BaseModel):
    pr_number: int = Field(description="Pull request number")
    comments: list[CodeReviewComment] = Field(description="List of review comments")
    code_overview: str = Field(
        description="Brief description of the pull request in markdown format with ### headers and bullet points."
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


class EditSuggestion(BaseModel):
    filename: str
    line_start: int
    line_end: int
    old_text: str
    new_text: str
    reasoning: str


class RevertPR(BaseModel):
    line_start: int
    line_end: int
    old_text: str
    new_text: str
    reasoning: str


class FunctionCall(BaseModel):
    """Represents a function call with its target and arguments"""

    target: str  # Entity ID for internal calls, function name for external
    full_call: str  # Complete call text with parameters
    is_internal: bool  # True if calling internal function, False if external


class CodeEntity(BaseModel):
    """Represents a code entity (function, class, method, etc.)"""

    id: str  # Unique identifier: "file_path:parent.name"
    name: str
    type: str  # function, class, method, variable, import, etc.
    file_path: str
    docstring: str | None = None
    signature: str | None = None
    decorators: list[str] = Field(default_factory=list)
    parent: str | None = None  # for methods, parent class
    calls: list[FunctionCall] = Field(default_factory=list)  # function calls made by this entity
    called_by: list[str] = Field(default_factory=list)  # entity IDs that call this entity
    start_line: int | None = None  # starting line number in file
    end_line: int | None = None  # ending line number in file


class FileAnalysis(BaseModel):
    """Analysis results for a single file"""

    file_path: str
    language: str
    entities: list[CodeEntity]
    imports: list[str]
    file_hash: str


class ProjectStructure(BaseModel):
    """High-level analysis of entire project"""

    name: str
    root_path: str
    total_files: int
    languages: dict[str, int]  # language -> file count
    file_analyses: list[FileAnalysis]
    architecture_summary: str
    key_components: list[dict[str, Any]] = Field(default_factory=list)
    call_graph: dict[str, list[str]] = Field(default_factory=dict)  # entity_id -> list of internal entity_ids it calls
    file_tree: str = Field(default="")
