from langchain.output_parsers import PydanticOutputParser
from models.models import CulpritPullRequests
from langchain_core.prompts import PromptTemplate

culprit_parser = PydanticOutputParser(pydantic_object=CulpritPullRequests)

template = """
You are an expert engineer helping diagnose a deploy blocker issue for Expensify's app repository - https://github.com/expensify/App
You will be given:
- A issue 
- A list of candidate pull requests (PRs) that have been merged into staging but not yet deployed to production. These PRs have been filtered to have semantic similarity with the issue title and steps.

Each issue includes:
- Title
- Steps to reproduce the issue

Each PR includes:
- PR id #
- Title
- Test steps
- Files Changed - List of files changed in the PR
- Code diff summary - a summary of what and why the code was changed
- Code diff - the actual code changes in diff format (truncated for readability)
- Score: Semantic similarity with the issue title and steps. This is between 0 and 1. Score above 0.5 is good but not always a culprit so look at lower scores too.
- Explanation (if available)

Your task is to find which PR might be responsible for the reported issue.

Instructions:

Analyze the PRs based on the issue reproduction steps and the test steps of each PR and title.
Do not make any guesses or assumptions about the issue or PRs.

Focus on the following criteria to determine if a PR is likely responsible for the issue:
1. UI/UX flows and transitions: If a PR alters components or logic used during the flow described in the bug (e.g., after submitting an expense), consider it more likely to be the culprit.
2. Compare the issue reproduction steps with the test steps of each PR.
3. Compare the keywords in issue title with PR test steps and PR title.
4. If a PR adds, removes, or swaps core components or logic responsible for the expected result, consider it very likely to affect observed behavior, even if the PR description only references a similar or edge-case flow.
5. Analyze the actual code diff to understand the technical changes made - look for modifications to functions, components, or logic that could directly impact the issue reproduction flow.
6. Provide the PRs most likely responsible for the issue.
7. If multiple PRs have a good score, reason which one is more likely to be the culprit.
8. Rank the PRs based on how the flow of issue reproduction steps matches with test steps of each PR.
9. Use both the code diff summary and the actual code diff to understand what changed and if they are related to the issue reproduction steps, consider it more likely to be the culprit.
10. PRs that change unrelated areas or cannot affect the described flow should not be considered.
11. Keep the reason concise and one sentence long and based on code diff analysis, code diff summary, and test steps.
12. Return top {culprits_to_find} most likely culprit PRs only.

Finally, sort based on most likely culprit PR for the issue and return the result as JSON matching this schema:

{format_instructions}

## Issue
ID: {issue_id}
Title: {issue_title}
Steps to Reproduce:
{issue_steps}

---

## Candidate PRs

{pull_requests_block}

"""

blame_prompt = PromptTemplate(
    template=template,
    input_variables=["issue_id", "issue_title", "issue_steps", "pull_requests_block", "culprits_to_find"],
    partial_variables={"format_instructions": culprit_parser.get_format_instructions()},
)
