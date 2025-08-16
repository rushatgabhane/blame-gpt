from enum import Enum


class CommandName(Enum):
    BLAME = "blame"
    CODE_REVIEW = "code_review"
    UNKNOWN = "unknown"

    # Used in LLM prompt to provide descriptions of commands
    def description(self) -> str:
        return {
            CommandName.BLAME: "find the culprit PR for an issue. find the PR that introduced this bug. Keywords: culprit, which PR, find PR, cause",
            CommandName.CODE_REVIEW: "perform a code review of a pull request. analyze code changes and provide detailed feedback. Keywords: review, feedback, analyze PR",
            CommandName.UNKNOWN: "no matching command",
        }[self]


class SecuritySeverity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class CodeReviewCommentType(Enum):
    NITPICK = "nitpick"
    SUGGESTION = "suggestion"
    ISSUE = "issue"
    TODO = "todo"
    THOUGHT = "thought"
    CHORE = "chore"
    NOTE = "note"
    PRAISE = "praise"
    SECURITY = "security"

    def description(self) -> str:
        return {
            CodeReviewCommentType.NITPICK: "Trivial preference-based request",
            CodeReviewCommentType.SUGGESTION: "Propose an improvement",
            CodeReviewCommentType.ISSUE: "Highlight a specific problem that should be addressed",
            CodeReviewCommentType.TODO: "Small, tedious, but necessary changes",
            CodeReviewCommentType.THOUGHT: "Share a non-actionable thought or idea",
            CodeReviewCommentType.CHORE: "Simple mechanical changes",
            CodeReviewCommentType.NOTE: "Highlight something important",
            CodeReviewCommentType.PRAISE: "Highlight something positive",
            CodeReviewCommentType.SECURITY: "Security issue found by automated tools",
        }[self]
