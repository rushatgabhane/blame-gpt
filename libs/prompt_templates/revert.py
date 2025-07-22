from langchain.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate

from models.models import RevertPR

revert_parser = PydanticOutputParser(pydantic_object=RevertPR)

template = """
    You are an experienced software engineer prolific in reverting problematic commits in a GitHub repo.
    I need help creating an intelligent revert for the following code changes.

    File: {filename}
    Original commit: {commit_hash}
    Commit message: {commit_message}

    Current file content:
    ```
    {file_content}
    ```

    Original changes that need to be reverted:
    ```diff
    {patch}
    ```

    Please analyze these changes and provide intelligent revert suggestions that:
    1. Safely revert the functionality while preserving any dependent changes
    2. Handle edge cases where a simple revert might break other code
    3. Suggest alternative approaches if a direct revert would be problematic
    4. Consider the semantic meaning of the changes, not just line-by-line reversal

    Respond with a JSON array of edit suggestions in this format:

    {format_instructions}
    """

revert_prompt = PromptTemplate(
    template=template,
    input_variables=["filename", "commit_hash", "commit_message", "file_content", "patch"],
    partial_variables={"format_instructions": revert_parser.get_format_instructions()},
)
