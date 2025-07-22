import json
import logging
import subprocess
from pathlib import Path

from github.Commit import Commit
from github.Repository import Repository

from libs.llm import llmReasoningCheap
from libs.prompt_templates.revert import revert_prompt
from models.models import EditSuggestion, FilePatch
from services.docs_service.sync import CLONE_DIR
from services.github import pull_request_service

logger = logging.getLogger(__name__)


def revert_with_ai(repo: Repository, pull_request_id: int, commit: Commit):
    """
    Perform AI-assisted revert of a pull request.
    """
    try:
        # 1. Get file patches from the original PR
        patches = pull_request_service.get_pull_request_patch(pull_request_id)

        if not patches:
            logger.info(f"No patches found for PR {pull_request_id}")
            return

        try:
            # 3. Send patches to AI and get edit suggestions
            edit_suggestions = get_ai_edit_suggestions(patches, commit)
            print(edit_suggestions)

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


def get_ai_edit_suggestions(patches: list[FilePatch], commit: Commit) -> list[EditSuggestion]:
    """
    Send patches to AI and get intelligent revert suggestions.
    """
    edit_suggestions: list[EditSuggestion] = []

    for patch in patches:
        # Prepare context for AI
        context = {
            "filename": patch.filename,
            "patch": patch.patch,
            "commit_message": commit.commit.message,
            "commit_hash": str(commit.sha),
            "file_content": _get_current_file_content(patch.filename),
        }

        prompt = revert_prompt.format(
            filename=context["filename"],
            commit_hash=context["commit_hash"],
            commit_message=context["commit_message"],
            file_content=context["file_content"],
            patch=context["patch"],
        )

        # Get AI response
        ai_response = llmReasoningCheap.invoke(prompt)

        # Parse AI suggestions
        suggestions = parse_ai_suggestions(str(ai_response.content), patch.filename)
        edit_suggestions.extend(suggestions)
        logger.debug(f"Generated {len(edit_suggestions)} edit suggestions")

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
    Apply edits to a specific file.
    """
    file_path = Path.joinpath(CLONE_DIR, filename)

    if not file_path.exists():
        logger.warning(f"File {filename} does not exist, skipping")
        return

    # Read current content
    with open(file_path, encoding="utf-8") as f:
        lines = f.readlines()

    # Sort suggestions by line number (descending to avoid offset issues)
    suggestions.sort(key=lambda x: x.line_start, reverse=True)

    # Apply each suggestion
    for suggestion in suggestions:
        try:
            # Convert to 0-based indexing
            start_idx = suggestion.line_start - 1
            end_idx = suggestion.line_end - 1

            # Replace the lines
            if suggestion.new_text:
                new_lines = suggestion.new_text.split("\n")
                lines[start_idx : end_idx + 1] = [line + "\n" for line in new_lines]
            else:
                # Delete lines
                del lines[start_idx : end_idx + 1]

            logger.info(
                f"Applied edit to {filename} lines {suggestion.line_start}-{suggestion.line_end}: {suggestion.reasoning}"
            )

        except IndexError as e:
            logger.warning(f"Error applying suggestion to {filename}: {e}")
            continue

    # Write modified content back
    with open(file_path, "w", encoding="utf-8") as f:
        f.writelines(lines)


def _get_current_file_content(filename: str) -> list[str]:
    """
    Get the current content of a file.
    """
    file_path = Path.joinpath(CLONE_DIR, filename)
    if not file_path.exists():
        logger.warning(f"File {filename} not found, returning empty content")
        return []

    with open(file_path, encoding="utf-8") as f:
        lines = f.readlines()

    return lines


def commit_ai_revert(pull_request_id: int):
    logger.info("Committing changes...")
    subprocess.run(["git", "-C", str(CLONE_DIR), "commit", "-am", f"Revert #{pull_request_id}"], check=True)
