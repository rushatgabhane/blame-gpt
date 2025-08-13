from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate

from models.models import CodeDiffSummary

code_diff_summary_parser = PydanticOutputParser(pydantic_object=CodeDiffSummary)

template = """
You are a senior software engineer in Expensify's App repository.

Read the TypeScript code diff below and write a concise pull-request description with exactly two sections:

### What Changed
• Summarize the key code changes (what was added, removed, or modified).
• Be specific but brief—focus on meaningful logic.

### Why It Changed
• Explain the intent or problem the changes address (bug fix, feature, refactor, perf, etc.).
• Base your reasoning only on clues in the diff (comments, test edits, variable names).
• Keep it factual. Do not invent context not present in the diff.


# PR details:
Title: {title}
Test Steps: {test}
Explanation: {explanation}
Code diff: {code_diff}


Return the output as JSON matching this schema:
{format_instructions}

"""


code_diff_summary_prompt = PromptTemplate(
    template=template,
    input_variables=[
        "title",
        "test",
        "explanation",
        "code_diff",
    ],
    partial_variables={"format_instructions": code_diff_summary_parser.get_format_instructions()},
    output_parser=code_diff_summary_parser,
)
