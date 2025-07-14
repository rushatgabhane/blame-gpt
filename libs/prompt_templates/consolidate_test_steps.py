from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate

from models.models import GeneratedTestStepsList

consolidate_test_steps_parser = PydanticOutputParser(pydantic_object=GeneratedTestStepsList)

template = """
You are a senior QA engineer that optimizes test steps for better readability and efficiency.
You are given a list of test steps that may have repetitive setup or similar initial steps.

# Instructions:
1. Keep the first test step with full details including all setup steps.
2. For subsequent test steps, only include the unique parts that differ from the first test.
3. If later tests have the same setup as the first test, start from the point where they differ.
4. Use numbered lists (1. 2. 3. etc.) for all steps.
5. Use arrows (→) for navigation between screens/sections to make it visually appealing.
6. Make steps concise while maintaining clarity.
7. Focus on the unique verification parts of each subsequent test.

# Original test steps:
{original_test_steps}

# Example of good consolidation:
Instead of:
Test 1: 
1. Login to app
2. Go to Settings
3. Enable Feature A
4. Verify Feature A works

Test 2:
1. Login to app
2. Go to Settings
3. Enable Feature B
4. Verify Feature B works

Consolidate to:
Test 1: Verify Feature A works
1. Login to app
2. Go to Settings
3. Enable Feature A
4. Verify Feature A works

Test 2: Verify Feature B works
1. Enable Feature B
2. Verify Feature B works

Return the consolidated test steps in the following format:
{format_instructions}

"""

consolidate_test_steps_prompt = PromptTemplate(
    template=template,
    input_variables=["original_test_steps"],
    partial_variables={"format_instructions": consolidate_test_steps_parser.get_format_instructions()},
    output_parser=consolidate_test_steps_parser,
)