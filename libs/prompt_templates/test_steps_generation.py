from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate

from models.models import TestStepsGeneration

test_steps_generation_parser = PydanticOutputParser(pydantic_object=TestStepsGeneration)

template = """"
You are a skilled QA engineer with expertise in software testing. You are tasked with generating test steps for a pull request on GitHub based on the provided details.

# Instructions:
1. You will be given the pull request's title, explanation of changes and a summary of the diff, i.e, the files that changed.
You need to analyse these details to understand what parts of the application have changed and how they affect the functionality.
2. Based on this understanding, your goal is to create a comprehensive set of test steps that cover the changes made in the pull request. 
3. The test steps should be clear, concise, and actionable, allowing a tester to verify the functionality introduced or modified by the pull request.
4. Think about how the human reviewing the PR would test the changes.
5. Write the test steps in markdown format, using bullet points or numbered lists for clarity.

# PR details:
Title: {title}
Explanation: {explanation}
Code Diff Summary: {diff_summary}

Return the output as JSON matching this schema:
{format_instructions}

"""

test_steps_prompt = PromptTemplate(
    template=template,
    input_variables=["title", "explanation", "diff_summary"],
    partial_variables={"format_instructions": test_steps_generation_parser.get_format_instructions()},
    output_parser=test_steps_generation_parser,
)
