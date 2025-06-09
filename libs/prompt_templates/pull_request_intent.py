from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser

from models.models import PullRequestIntent

pull_request_intent_parser = PydanticOutputParser(pydantic_object=PullRequestIntent)

template = """
You are an expert in Expensify's App repository. 

# Instructions:
1. You are given PR details. Provide a summary of the main purpose of the PR.
2. This summary will be used to find relevant user facing help articles and suggest updates to them.
3. Focus on understanding the user impact. Focus on user facing changes and behavioral updates to the app.
4. This changed UI strings may not be relevant (eg: tooltips, error messages, etc).
5. Classify if the PR is a bug fix.

### Only include changes that affect:
- What the user must do
- What the user sees in terms of flow or functionality
- The presence or removal of features, steps, or options
Think like a user: If reading the help article, what would they now need to do differently?
If the PR does not change user behavior or functionality, return "No user impact".

### Bug fixes are changes that:
- Fix an existing feature that was broken or not working as intended
- Restore functionality that was previously available but stopped working
- Refactoring, optimization, performance improvement etc.
- Visual tweaks, layout changes, or rendering fixes
- Label, tooltip, or icon updates unless behavior also changed

# PR details:
Title: {title}
Test Steps: {test}
Explanation: {explanation}
Changed UI strings: {en_patch}


Return the output as JSON matching this schema:
{format_instructions}

"""


pull_request_intent_prompt = PromptTemplate(
    template=template,
    input_variables=[
        "title",
        "test",
        "explanation",
        "en_patch",
    ],
    partial_variables={"format_instructions": pull_request_intent_parser.get_format_instructions()},
    output_parser=pull_request_intent_parser,
)
