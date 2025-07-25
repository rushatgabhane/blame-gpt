import json
import logging
import subprocess
from pathlib import Path

from github.PullRequest import PullRequest

from libs.llm import llmCodingModelCheapKimi
from libs.prompt_templates.revert import revert_prompt
from models.models import EditSuggestion, FilePatch
from services.docs_service.sync import CLONE_DIR
from services.github import pull_request_service

logger = logging.getLogger(__name__)


def revert_with_ai(pull_request: PullRequest):
    """
    Perform AI-assisted revert of a pull request.
    """
    pull_request_id = pull_request.number
    try:
        # 1. Get file patches from the original PR
        patches = pull_request_service.get_pull_request_patch(pull_request_id)

        if not patches:
            logger.info(f"No patches found for PR {pull_request_id}")
            return

        try:
            # 3. Send patches to AI and get edit suggestions
            edit_suggestions = get_ai_edit_suggestions(patches, pull_request)
            logger.debug(f"AI edit suggestions: \n{edit_suggestions}")

            # 4. Apply AI-suggested edits
            apply_edit_suggestions(edit_suggestions)

            # 5. Commit the changes
            commit_ai_revert(pull_request_id)

        except Exception as e:
            logger.error(f"failed to process PR {pull_request_id}: {e}")
            return

    except Exception as e:
        logger.error(f"Error during AI revert: {e}")
        return


def get_ai_edit_suggestions(file_patches: list[FilePatch], pull_request: PullRequest) -> list[EditSuggestion]:
    """
    Send patches to AI and get intelligent revert suggestions.
    """
    edit_suggestions: list[EditSuggestion] = []

    for file_patch in file_patches:
        # Prepare context for AI
        context = {
            "filename": file_patch.filename,
            "patch": file_patch.patch,
            "pull_request_title": pull_request.title,
            "pull_request_body": pull_request.body,
            "commit_hash": pull_request.merge_commit_sha,
            "file_content": _get_current_file_content(file_patch.filename),
        }

        prompt = revert_prompt.format(
            filename=context["filename"],
            commit_hash=context["commit_hash"],
            pull_request_body=context["pull_request_body"],
            pull_request_title=context["pull_request_title"],
            file_content=context["file_content"],
            patch=context["patch"],
        )

        # Get AI response
        ai_response = llmCodingModelCheapKimi.invoke(prompt)
        ai_response_clean = str(ai_response.content).replace("json", "").replace("```", "")
        # ai_response_clean = ""
        print(ai_response_clean)
        print(type(ai_response_clean))

        # Parse AI suggestions
        suggestions = parse_ai_suggestions(ai_response_clean, file_patch.filename)
        edit_suggestions.extend(suggestions)

    return edit_suggestions


def parse_ai_suggestions(ai_response: str, filename: str) -> list[EditSuggestion]:
    """
    Parse AI response into EditSuggestion objects.
    """
    try:
        suggestions_data = json.loads(ai_response)

        suggestions = []

        for suggestion in suggestions_data:
            suggestions.append(
                EditSuggestion(
                    filename=filename,
                    line_start=suggestion["line_start"],
                    line_end=suggestion["line_end"],
                    old_text=suggestion["old_text"],
                    new_text=suggestion["new_text"],
                    reasoning=suggestion["reasoning"],
                )
            )

        return suggestions

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse AI response: {e}")
        # Fallback to simple revert if AI parsing fails
        return []


def apply_edit_suggestions(suggestions: list[EditSuggestion]):
    """
    Apply AI-suggested edits to the files.
    """
    # Group suggestions by filename
    files_to_edit: dict[str, list[EditSuggestion]] = {}
    for suggestion in suggestions:
        if suggestion.filename not in files_to_edit:
            files_to_edit[suggestion.filename] = []
        files_to_edit[suggestion.filename].append(suggestion)

    # Apply edits to each file
    for filename, file_suggestions in files_to_edit.items():
        _apply_file_edits(filename, file_suggestions)


def _apply_file_edits(filename: str, suggestions: list[EditSuggestion]):
    """
    Apply edits to a specific file, handling line number shifts correctly.
    """
    file_path = Path.joinpath(CLONE_DIR, filename)

    if not file_path.exists():
        print(f"Warning: File {filename} does not exist, skipping")
        return

    # Read current content
    with open(file_path, encoding="utf-8") as f:
        content = f.read()

    # Convert suggestions to character-based offsets for more reliable editing
    char_based_edits = convert_to_char_offsets(content, suggestions)

    # Sort by character offset (descending to avoid offset issues)
    char_based_edits.sort(key=lambda x: x["start_offset"], reverse=True)

    # Apply each edit
    for edit in char_based_edits:
        try:
            start_offset = edit["start_offset"]
            end_offset = edit["end_offset"]
            new_text = edit["new_text"]

            # Apply the edit
            content = content[:start_offset] + new_text + content[end_offset:]

            print(
                f"Applied edit to {filename} lines {edit['original_line_start']}-{edit['original_line_end']}: {edit['reasoning']}"
            )

        except Exception as e:
            print(f"Error applying suggestion to {filename}: {e}")
            continue

    # Write modified content back
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)


def convert_to_char_offsets(content: str, suggestions: list[EditSuggestion]) -> list[dict]:
    """
    Convert line-based suggestions to character-based offsets.
    This makes edits more reliable when multiple changes are applied.
    """
    lines = content.split("\n")
    char_based_edits = []

    for suggestion in suggestions:
        try:
            start_line = suggestion.line_start
            end_line = suggestion.line_end

            # Validate line numbers
            if start_line < 0 or end_line >= len(lines) or start_line > end_line:
                print(
                    f"Warning: Invalid line range {suggestion.line_start}-{suggestion.line_end} for file {suggestion.filename}"
                )
                continue

            # Calculate character offsets
            start_offset = sum(len(lines[i]) + 1 for i in range(start_line))  # +1 for newline
            end_offset = sum(len(lines[i]) + 1 for i in range(end_line + 1))

            # Adjust for the last line if it doesn't end with newline
            if end_line == len(lines) - 1 and not content.endswith("\n"):
                end_offset -= 1

            # Handle newlines in replacement text
            new_text = suggestion.new_text if suggestion.new_text else ""

            char_based_edits.append(
                {
                    "start_offset": start_offset,
                    "end_offset": end_offset,
                    "new_text": new_text,
                    "original_line_start": suggestion.line_start,
                    "original_line_end": suggestion.line_end,
                    "reasoning": suggestion.reasoning,
                }
            )

        except Exception as e:
            print(f"Error converting suggestion to char offset: {e}")
            continue

    return char_based_edits


def _get_current_file_content(filename: str) -> str:
    """
    Get the current content of a file.
    """
    file_path = Path.joinpath(CLONE_DIR, filename)
    if not file_path.exists():
        logger.warning(f"File {filename} not found, returning empty content")
        return ""

    with open(file_path, encoding="utf-8") as f:
        lines = f.read()

    return lines


def commit_ai_revert(pull_request_id: int):
    logger.info("Committing changes...")
    try:
        subprocess.run(["git", "-C", str(CLONE_DIR), "commit", "-am", f"Revert #{pull_request_id}"], check=True)
        logger.info(f"Successfully committed revert for PR #{pull_request_id}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to commit revert for PR #{pull_request_id}: {e}")
        return
