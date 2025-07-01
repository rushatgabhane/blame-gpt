from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate

from models.models import DocEditEvaluation

doc_edit_evaluation_parser = PydanticOutputParser(pydantic_object=DocEditEvaluation)

template = """
You are reviewing whether Expensify's Help articles need updates based on a pull request change.
We don't want articles to be outdated or incorrect.

You are given:
- A summary of the pull request
- Suggested edits to one or more help articles

# Instructions:
2. Your task is to evaluate if the suggested edits are necessary and meaningful from a user's perspective.
3. Only suggest edits if there is **missing or incorrect information** in the help article.
4. Do NOT suggest edits that only improve wording or structure.
5. Do NOT duplicate content that is already correct, even if it's phrased differently.
6. Prefer minimal and high impact edits. Skip minor edits that just clarify already correct information or add small details that don't matter from a user's perspective.
7. Set should_docs_update to true if the edits are necessary, otherwise set it to false.
8. If should_docs_update is true, provide a list of necessary edits to apply in the `edits_to_apply` field.
9. Provide a consise reason for your decision.

Reject suggestions like:
❌ Bug fixes
❌ “Markdown rendering of underscores has improved”
❌ “Buttons are now slightly larger”
❌ “Line breaks render more cleanly”
These are not documentation-worthy users don't need to to act differently.


Pull request summary:
{intent}

Suggested article edits (in JSON):
{suggestions_json}

Respond with a JSON in this format:
{format_instructions}
"""

doc_edit_evaluation_prompt = PromptTemplate(
    template=template,
    input_variables=["intent", "suggestions_json"],
    partial_variables={"format_instructions": doc_edit_evaluation_parser.get_format_instructions()},
)
