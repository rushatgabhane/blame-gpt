import asyncio
import json
import logging

from models.models import PRFileDiff, SecurityFinding

logger = logging.getLogger(__name__)


async def run_security_analysis(repo_path: str | None, pr_diffs: list[PRFileDiff]) -> list[SecurityFinding]:
    if not repo_path:
        return []

    changed_files = [diff.filename for diff in pr_diffs if diff.patch]
    if not changed_files:
        return []

    bandit_task = asyncio.create_task(_run_bandit(repo_path, changed_files))
    gosec_task = asyncio.create_task(_run_gosec(repo_path, changed_files))

    python_findings, go_findings = await asyncio.gather(bandit_task, gosec_task)

    all_findings = python_findings + go_findings

    severity_order = {"high": 0, "medium": 1}
    all_findings.sort(key=lambda x: severity_order.get(x.severity, 2))

    return all_findings


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

        stdout, stderr = await process.communicate()

        if stdout:
            data = json.loads(stdout.decode())

            for issue in data["results"]:
                severity = issue["issue_severity"].lower()
                if severity in ["high", "medium"]:
                    line_range = issue.get("line_range", [issue["line_number"]])
                    finding = SecurityFinding(
                        file_path=issue["filename"],
                        line=max(line_range),
                        start_line=min(line_range) if len(line_range) > 1 else None,
                        severity=severity,
                        rule_id=issue["test_id"],
                        description=issue["issue_text"],
                        tool="bandit",
                    )
                    findings.append(finding)

    except Exception as e:
        logger.warning(f"Bandit analysis failed: {e}")

    return findings


async def _run_gosec(repo_path: str, changed_files: list[str]) -> list[SecurityFinding]:
    """Run Gosec security analysis on changed Go files."""
    findings: list[SecurityFinding] = []

    go_files = [f for f in changed_files if f.endswith(".go")]
    if not go_files:
        return findings

    try:
        process = await asyncio.create_subprocess_exec(
            "gosec",
            "-fmt=json",
            "-severity=medium",
            "./...",
            cwd=repo_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await process.communicate()

        if stdout:
            data = json.loads(stdout.decode())

            for issue in data["Issues"]:
                if any(issue["file"].endswith(f) for f in go_files):
                    severity = issue["severity"].lower()
                    if severity in ["high", "medium"]:
                        line_num = int(issue["line"])
                        finding = SecurityFinding(
                            file_path=issue["file"],
                            line=line_num,
                            start_line=None,
                            severity=severity,
                            rule_id=issue["rule_id"],
                            description=issue["details"],
                            tool="gosec",
                        )
                        findings.append(finding)

    except Exception as e:
        logger.warning(f"Gosec analysis failed: {e}")

    return findings
