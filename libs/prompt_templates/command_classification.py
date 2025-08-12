from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate

from models.enums import CommandName
from models.models import CommandClassification

command_classification_parser = PydanticOutputParser(pydantic_object=CommandClassification)

available_commands = "\n".join(f"{cmd.value}: {cmd.description()}" for cmd in CommandName)

template = """
You are given a comment from a user on a GitHub issue or pull request.
Your task is to classify the comment into one of the following commands:

{available_commands}

The comment may contain additional content like PR descriptions, or other discussions.
Look for specific command keywords that match the available commands above.
Ignore the "{user_tag}" tag itself when classifying - do not use words from the tag for command classification.

The comment is as follows:
{comment}

The type (issue or pull request) is: {type}

Return the output as JSON matching this schema:
{format_instructions}
"""

command_classifier_prompt = PromptTemplate(
    template=template,
    input_variables=["comment", "type", "user_tag"],
    partial_variables={
        "available_commands": available_commands,
        "format_instructions": command_classification_parser.get_format_instructions(),
    },
    output_parser=command_classification_parser,
)
