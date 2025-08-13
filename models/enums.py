from enum import Enum


class CommandName(Enum):
    BLAME = "blame"
    OHMYDOCS = "ohmydocs"
    TEST_STEPS = "test_steps"
    CODE_REVIEW = "code_review"
    UNKNOWN = "unknown"

    # Used in LLM prompt to provide descriptions of commands
    def description(self) -> str:
        return {
            CommandName.BLAME: "find the culprit PR for an issue. find the PR that introduced this bug. Keywords: culprit, which PR, find PR, cause",
            CommandName.OHMYDOCS: "suggest HelpDot docs changes that need updating in this PR. generate documentation updates for a PR. Keywords: docs, documentation, helpdot",
            CommandName.TEST_STEPS: "write test steps a reviewer should follow. generate test steps for a PR for a reviewer or QA. Keywords: QA steps, testing steps",
            CommandName.CODE_REVIEW: "perform a code review of a pull request. analyze code changes and provide detailed feedback. Keywords: review, feedback, analyze PR",
            CommandName.UNKNOWN: "no matching command",
        }[self]


class CodeReviewCommentType(Enum):
    NITPICK = "nitpick"
    SUGGESTION = "suggestion"
    ISSUE = "issue"
    TODO = "todo"
    THOUGHT = "thought"
    CHORE = "chore"
    NOTE = "note"
    PRAISE = "praise"

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
        }[self]
