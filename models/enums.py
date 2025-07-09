from enum import Enum


class CommandName(Enum):
    BLAME = "blame"
    OHMYDOCS = "ohmydocs"
    TEST_STEPS = "test_steps"
    UNKNOWN = "unknown"

    # Used in LLM prompt to provide descriptions of commands
    def description(self) -> str:
        return {
            CommandName.BLAME: "find the culprit PR for an issue. find the PR that introduced this bug.",
            CommandName.OHMYDOCS: "suggest HelpDot docs changes that need updating in this PR. generate documentation updates for a PR.",
            CommandName.TEST_STEPS: "write test steps a reviewer should follow. generate test steps for a PR for a reviewer or QA.",
            CommandName.UNKNOWN: "no matching command",
        }[self]
