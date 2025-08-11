# From a given issue body, find or generate test steps that can be used to test the linked PR for the issue.
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate

from models.models import GeneratedTestSteps

issue_steps_for_bug_parser = PydanticOutputParser(pydantic_object=GeneratedTestSteps)

template = """
You are a senior QA engineer that writes test steps for Expensify's App.
You are given a issue title, and issue body that describes a bug.
A issue body may contain a precondition, action performed, actual outcome and expected outcome.

# Instructions:
1. Use the given precondition, action performed, actual outcome and **expected outcome** to write test steps.
2. The test steps should have "verify" statements that check the expected outcome.
3. The test steps should be clear, concise, and easy to follow by a QA who will test the PR that fixes the issue.
4. The test steps should be numbered list.
5. Use arrows (→) for navigation between screens/sections to make it visually appealing.
6. Don't say staging.expensify.com. Say App only.

### Example test steps:

Precondition: At least one workspace member is assigned a VISA card and WS is connected to QBO.
Title: Verify that QBO export works for VISA card transactions.
1. Login to App
2. Go to workspace settings → Members
3. Click on the member with VISA card
4. Click on the card
5. Click QuickBooks Online credit card export
6. Verify that the export is successful and the VISA card transactions are exported to QBO


# Issue details:
Title: {title}
Body: {body}


Return the test steps in the following format:
{format_instructions}

"""

issue_steps_for_bug_prompt = PromptTemplate(
    template=template,
    input_variables=["title", "body"],
    partial_variables={"format_instructions": issue_steps_for_bug_parser.get_format_instructions()},
    output_parser=issue_steps_for_bug_parser,
)
