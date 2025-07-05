import os

from langchain.output_parsers import OutputFixingParser, PydanticOutputParser
from langchain.prompts import PromptTemplate

from libs import llmFactory, modeltypeenums
from models.models import DocUpdateDiff

ai_env = os.getenv("LLM_TYPE", "open-ai")

_raw_parser = PydanticOutputParser(pydantic_object=DocUpdateDiff)
llmReasoningCheap = llmFactory.llmFactory().getLLM(
    ai_env,
    False,
    modelType=modeltypeenums.ModelThinkingType.REASONING,
    cost=modeltypeenums.ModelCostType.CHEAP,
)
doc_edit_parser = OutputFixingParser.from_llm(parser=_raw_parser, llm=llmReasoningCheap)


template = """
You are a documentation assistant for Expensify's user facing help articles - help.expensify.com

Instructions:
1. You are given a summary of a pull request and a help article.
2. Your task is to suggest updates to the help article based on the pull request summary. 
3. If no updates are needed, return an empty list for `edits`.
4. You must output a valid JSON object only. Do not use + to concatenate strings. Multiline strings should be inlined with \n.
5. Only suggest edits that are factually necessary. e.g. a new feature, updated UI behavior, or missing information.

You are NOT expected to rewrite every UI string or reflect minor onboarding copy changes. Focus only on:
- Major behavioral differences
- Steps the user must now do differently
- Features added or removed
- Major wording that may mislead users

Do NOT suggest edits for:
- Bug fixes
- New improvements to software that do not change user behavior
- Minor UI changes that do not affect user actions
- New technical software improvements
- Stylistic changes like tone, clarity, grammar, rewording
- Existing steps just to improve writing

Pull request summary:
{intent}

Here is a Help article:
Path: {path}
Content: {content}


If an update is needed, identify the specific part that should change and suggest the updated version.
Return only a JSON object with this format:

{format_instructions}
"""

doc_edit_suggestions_prompt = PromptTemplate(
    template=template,
    input_variables=["intent", "path", "content"],
    partial_variables={"format_instructions": doc_edit_parser.get_format_instructions()},
)
