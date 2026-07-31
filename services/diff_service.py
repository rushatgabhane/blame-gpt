import re

from models.models import FormattedDiffs, PRFileDiff


def format_pr_diffs_for_review(pr_diffs: list[PRFileDiff]) -> FormattedDiffs:
    """Format PR diffs with embedded line numbers and track changed lines"""
    formatted_diffs = []
    changed_lines_map: dict[str, set[int]] = {}

    for diff in pr_diffs:
        if not diff.patch:
            continue

        formatted_diff = f"## File: {diff.filename}\n"
        formatted_diff += f"Status: {diff.status}\n"
        formatted_diff += f"Changes: +{diff.additions} -{diff.deletions}\n\n"

        numbered_patch, changed_lines = _add_line_numbers_to_patch(diff.patch)

        changed_lines_map[diff.filename] = changed_lines
        formatted_diff += numbered_patch
        formatted_diffs.append(formatted_diff)

    return FormattedDiffs(diff="\n\n".join(formatted_diffs), file_line_number_changed_map=changed_lines_map)


def _add_line_numbers_to_patch(patch: str) -> tuple[str, set[int]]:
    lines = patch.split("\n")
    numbered_lines: list[str] = []
    changed_lines: set[int] = set()
    current_new_line = None

    for line in lines:
        # Skip empty lines at the end
        if not line:
            numbered_lines.append(line)
            continue

        # Parse hunk headers to get starting line numbers
        if line.startswith("@@"):
            # Extract new file line number from hunk header like "@@ -10,7 +10,8 @@"
            match = re.search(r"@@\s*-\d+,?\d*\s*\+(\d+),?\d*\s*@@", line)
            if match:
                current_new_line = int(match.group(1))
            numbered_lines.append(line)  # Keep hunk headers as is
            continue

        # Skip file headers
        if line.startswith("+++") or line.startswith("---"):
            numbered_lines.append(line)
            continue

        # Only process if we have a valid starting line number
        if current_new_line is None:
            numbered_lines.append(line)
            continue

        if line.startswith("-"):
            # Don't number removed lines, don't increment counter
            numbered_lines.append(line)
        elif line.startswith("+"):
            # Number added lines with actual file line number
            numbered_lines.append(f"{current_new_line} {line}")
            changed_lines.add(current_new_line)
            current_new_line += 1
        else:
            # Context line (unchanged) - number with actual file line number
            numbered_lines.append(f"{current_new_line} {line}")
            current_new_line += 1

    return "\n".join(numbered_lines), changed_lines


def split_raw_diff(raw_diff: str) -> dict[str, str]:
    """Split one raw unified diff into per-file patches keyed by the new file path."""
    patches: dict[str, str] = {}
    header = re.compile(r"^diff --git a/(.*?) b/(.*)$")
    filename: str | None = None
    current: list[str] = []

    for line in raw_diff.splitlines():
        match = header.match(line)
        if match:
            if filename:
                patches[filename] = "\n".join(current)
            filename = match.group(2)
            current = []
            continue
        if filename is None:
            continue
        current.append(line)

    if filename:
        patches[filename] = "\n".join(current)

    return patches
