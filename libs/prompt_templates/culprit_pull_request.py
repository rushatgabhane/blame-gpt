from langchain.output_parsers import PydanticOutputParser
from models.models import CulpritPullRequests
from langchain_core.prompts import PromptTemplate

culprit_parser = PydanticOutputParser(pydantic_object=CulpritPullRequests)

template = """
You are an expert engineer helping diagnose a deploy blocker issue for Expensify's app repository - https://github.com/expensify/App
You will be given:
- A issue 
- A list of candidate pull requests (PRs) that have been merged into staging but not yet deployed to production.

Each issue includes:
- Title
- Steps to reproduce the issue

Each PR includes:
- Title
- Test steps
- List of changed files
- Explanation (if available)

Your task is to carefully analyze if a PR might be responsible for the reported issue.

Instructions:

Do not predict if the PR could be culprit based on some reason. Just analyze the PRs based on the issue reproduction steps and the test steps of each PR and title.
eg: This PR addresses report sorting, which might impact how reports are displayed, including potentially empty states in the reports page.
Do not make any guesses or assumptions about the issue or PRs.

Focus on the following criteria to determine if a PR is likely responsible for the issue:
1. UI/UX flows and transitions: If a PR alters components or logic used during the flow described in the bug (e.g., after submitting an expense), consider it more likely to be the culprit.
2. Compare the issue reproduction steps with the test steps of each PR.
3. Compare the keywords in issue title with PR test steps and PR title.
4. If a PR adds, removes, or swaps core components or logic responsible for the expected result, consider it very likely to affect observed behavior, even if the PR description only references a similar or edge-case flow.
5. Provide the PRs most likely responsible for the issue.
6. Give a score from 0 to 100 percent how much the flow of issue reproduction steps matches with test steps of each PR and put it in the score field.
6. See the files changed in each PR and if they are related to the issue reproduction steps, consider it more likely to be the culprit. 
7. PRs that change unrelated areas or cannot affect the described flow should not be considered.
8. If scores are similar, prefer PRs that have more files changed.
9. Use explaination field of PRs to understand the context of the PR. If it is unrelated to the issue, do not consider it as a culprit.
10. If no keyword matches are found, do not consider the PR as a culprit.

Finally, sort the PRs by their score in descending order, skip score less than 50 and return the result as JSON matching this schema:

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
    input_variables=["issue_id", "issue_title", "issue_steps", "pull_requests_block"],
    partial_variables={"format_instructions": culprit_parser.get_format_instructions()},
)
