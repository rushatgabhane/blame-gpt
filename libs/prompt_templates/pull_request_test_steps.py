from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate

from models.models import GeneratedTestStepsList

test_steps_generation_parser = PydanticOutputParser(pydantic_object=GeneratedTestStepsList)

template = """
You are a senior software engineer that writes test steps for PRs in Expensify's App repository.
You are tasked with writing test **steps** for a pull request, so that QA engineers can verify your PR.

# Given:
1. PR (pull request) details for which test steps are to be written.
2. Test steps from the linked issue for the PR. This has the most importance for writing test steps.
3. Similar test steps from the QA test suite of Expensify. Use these as a reference.
4. Instead of staging.expensify.com use app.

# Instructions:
1. Generate test steps based on the PR details so that QA engineers can verify your PR.
2. Use the provided PR title and code diff summary to write the test steps for QA.
3. Use the given linked issue test steps, and similar test steps from the QA test suite as references.
4. The test steps should be concise.
5. Use numbered lists for the steps.
6. Generate more than one test only if there are multiple cases to verify. Avoid repeating between test steps.

# Linked issue test steps (This is most important):
{linked_issue_test_steps}

# Similar test steps from QA test suite:
{similar_test_steps}

# PR details:
Title: {title}
Code Diff Summary: {diff_summary}

Return the output as JSON matching this schema:
{format_instructions}

"""

test_steps_prompt = PromptTemplate(
    template=template,
    input_variables=[
        "linked_issue_test_steps",
        "similar_test_steps",
        "title",
        "diff_summary",
    ],
    partial_variables={"format_instructions": test_steps_generation_parser.get_format_instructions()},
    output_parser=test_steps_generation_parser,
)
