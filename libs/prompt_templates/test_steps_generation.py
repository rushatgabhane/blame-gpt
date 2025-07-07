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
6. Ensure that you write nothing but only the steps that need to followed to test the changes made in the PR.

# Example test steps:
Here is an example of how the test steps should look like:

Tests

1.  Go to [https://staging.new.expensify.com/home](https://staging.new.expensify.com/home)
2.  Go to workspace settings - enable tags - upload dependant tags with GL code
3.  Toggle on - There is a GL code in adjacent column
4.  Toggle off these are independent tags & first row is the title for each tag list
5.  Tap next - got it
6.  Tap sub projects - city or any item in the list
7.  Tapping on sub projects tag, note that it's display without hmm not here.


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
