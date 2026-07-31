import asyncio
import json
import logging

from models.enums import SecuritySeverity
from models.models import PRFileDiff, SecurityFinding

logger = logging.getLogger(__name__)


async def run_security_analysis(
    repo_path: str | None, pr_diffs: list[PRFileDiff], file_line_number_changed_map: dict[str, set[int]]
) -> list[SecurityFinding]:
    if not repo_path:
        return []

    changed_files = [diff.filename for diff in pr_diffs if diff.patch]
    if not changed_files:
        return []

    all_findings = await _run_bandit(repo_path, changed_files)

    filtered_findings = []
    for finding in all_findings:
        file_changed_lines = file_line_number_changed_map.get(finding.file_path, set())
        if finding.line in file_changed_lines:
            filtered_findings.append(finding)
    return filtered_findings


async def _run_bandit(repo_path: str, changed_files: list[str]) -> list[SecurityFinding]:
    """Run Bandit security analysis on changed Python files."""
    findings: list[SecurityFinding] = []

    python_files = [f for f in changed_files if f.endswith(".py")]
    if not python_files:
        return findings

    try:
        process = await asyncio.create_subprocess_exec(
            "bandit",
            "-f",
            "json",
            "--severity-level",
            "medium",
            *python_files,
            cwd=repo_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, _ = await process.communicate()
        if not stdout:
            return findings

        data = json.loads(stdout.decode())

        for issue in data["results"]:
            severity = SecuritySeverity(issue["issue_severity"].lower())
            if severity == SecuritySeverity.LOW:
                continue

            line_range = issue.get("line_range", [issue["line_number"]])
            file_path = issue["filename"]
            relative_file_path = file_path[2:] if file_path.startswith("./") else file_path
            finding = SecurityFinding(
                file_path=relative_file_path,
                line=max(line_range),
                start_line=min(line_range) if len(line_range) > 1 else None,
                severity=severity,
                rule_id=issue["test_id"],
                description=issue["issue_text"],
                tool="bandit",
            )
            findings.append(finding)

    except Exception as e:
        logger.error(f"python bandit security analysis failed: {e}")

    return findings
