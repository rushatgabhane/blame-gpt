"""
PR Dependency Analysis Pipeline

Analyzes dependency changes in pull requests and provides detailed reports
on added, removed, and updated dependencies across multiple languages.
"""

import logging
import tempfile
from collections.abc import AsyncGenerator
from pathlib import Path

from github.Repository import Repository

from dependency_analyzer import DiffAnalyzer, DiffReport
from libs.constants import SIGNATURE
from libs.sqlite.core.core_sqlite_client import Database
from services.github.comment_service import post_comment_on_issue_or_pr

logger = logging.getLogger(__name__)


async def run(
    pull_request_id: int,
    repo_client: Repository,
    db: Database,
    usage_log_id: int | None = None,
) -> AsyncGenerator[str]:
    """
    Analyze dependency changes in a PR and post results as a comment.
    
    Args:
        pull_request_id: GitHub PR number
        repo_client: GitHub repository client
        db: Database instance for tracking
        usage_log_id: Usage tracking ID
        
    Yields:
        Progress updates for logging
    """
    try:
        yield f"Starting dependency analysis for PR #{pull_request_id}"
        
        # Get PR details and diffs
        pr = repo_client.get_pull(pull_request_id)
        yield f"Fetched PR details: {pr.title}"
        
        # Get PR diff content
        diff_url = pr.diff_url
        yield f"Getting PR diff from: {diff_url}"
        
        # Analyze dependency changes using our diff analyzer
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Initialize diff analyzer
            diff_analyzer = DiffAnalyzer()
            yield "Initialized dependency diff analyzer"
            
            # Analyze the PR diff
            diff_report = await _analyze_pr_dependencies(
                diff_analyzer, pr, temp_path, usage_log_id
            )
            yield f"Analyzed dependencies: found {diff_report.total_changes} changes"
            
            if diff_report.total_changes == 0:
                yield "No dependency changes found"
                comment_body = _format_no_changes_comment()
            else:
                yield f"Formatting report with {diff_report.total_changes} changes"
                comment_body = _format_dependency_report(diff_report, pr.title)
            
            # Post comment to PR
            yield "Posting dependency analysis comment to PR"
            post_comment_on_issue_or_pr(
                issue_or_pr_number=pull_request_id,
                comment_body=comment_body,
                repo_client=repo_client
            )
            
            yield f"Successfully completed dependency analysis for PR #{pull_request_id}"
            
    except Exception as e:
        error_msg = f"Failed to analyze dependencies for PR #{pull_request_id}: {str(e)}"
        logger.exception(error_msg)
        
        # Post error comment
        error_comment = f"❌ **Dependency Analysis Failed**\n\n{error_msg}\n\n{SIGNATURE}"
        try:
            post_comment_on_issue_or_pr(
                issue_or_pr_number=pull_request_id,
                comment_body=error_comment,
                repo_client=repo_client
            )
        except Exception as comment_error:
            logger.error(f"Failed to post error comment: {comment_error}")
        
        yield f"Error: {error_msg}"


async def _analyze_pr_dependencies(
    diff_analyzer: DiffAnalyzer, 
    pr, 
    temp_path: Path, 
    usage_log_id: int | None
) -> DiffReport:
    """Analyze dependencies in a PR using GitHub PR URL."""
    try:
        # Use the diff analyzer's GitHub PR analysis feature
        github_token = None  # Will use environment variable
        pr_url = pr.html_url
        
        # Analyze the PR using our existing diff analyzer
        diff_report = diff_analyzer.analyze_pr_diff(
            pr_url=pr_url, 
            github_token=github_token
        )
        
        return diff_report
        
    except Exception as e:
        logger.error(f"Failed to analyze PR dependencies: {e}")
        # Return empty diff report
        return DiffReport(
            project_name=pr.base.repo.name,
            project_path=temp_path,
            base_ref="main",
            head_ref="HEAD",
            added=[],
            removed=[],
            updated=[]
        )


def _format_dependency_report(diff_report: DiffReport, pr_title: str) -> str:
    """Format the dependency analysis results as a GitHub comment."""
    
    comment_parts = [
        "## 📦 Dependency Analysis Results",
        f"**Pull Request:** {pr_title}",
        f"**Total Changes:** {diff_report.total_changes}",
        ""
    ]
    
    # Summary section
    if diff_report.added or diff_report.removed or diff_report.updated:
        comment_parts.extend([
            "### 📊 Summary",
            f"- ➕ **Added:** {len(diff_report.added)} dependencies",
            f"- ➖ **Removed:** {len(diff_report.removed)} dependencies", 
            f"- 🔄 **Updated:** {len(diff_report.updated)} dependencies",
            ""
        ])
    
    # Added dependencies
    if diff_report.added:
        comment_parts.extend([
            "### ➕ Added Dependencies",
            "| Name | Version | Language | Type | Source File |",
            "|------|---------|----------|------|-------------|"
        ])
        for dep in sorted(diff_report.added, key=lambda x: (x.language.value, x.name)):
            comment_parts.append(
                f"| `{dep.name}` | `{dep.version}` | {dep.language.value} | {dep.dependency_type.value} | `{dep.source_file.name}` |"
            )
        comment_parts.append("")
    
    # Removed dependencies
    if diff_report.removed:
        comment_parts.extend([
            "### ➖ Removed Dependencies", 
            "| Name | Version | Language | Type | Source File |",
            "|------|---------|----------|------|-------------|"
        ])
        for dep in sorted(diff_report.removed, key=lambda x: (x.language.value, x.name)):
            comment_parts.append(
                f"| `{dep.name}` | `{dep.version}` | {dep.language.value} | {dep.dependency_type.value} | `{dep.source_file.name}` |"
            )
        comment_parts.append("")
    
    # Updated dependencies
    if diff_report.updated:
        comment_parts.extend([
            "### 🔄 Updated Dependencies",
            "| Name | Old Version → New Version | Language | Type | Source File |",
            "|------|---------------------------|----------|------|-------------|"
        ])
        for dep_change in sorted(diff_report.updated, key=lambda x: (x.old_dependency.language.value, x.old_dependency.name)):
            old_dep = dep_change.old_dependency
            new_dep = dep_change.new_dependency
            comment_parts.append(
                f"| `{old_dep.name}` | `{old_dep.version}` → `{new_dep.version}` | {old_dep.language.value} | {old_dep.dependency_type.value} | `{old_dep.source_file.name}` |"
            )
        comment_parts.append("")
    
    # Footer with instructions
    comment_parts.extend([
        "---",
        "💡 **Need a detailed analysis?** Use `@BlameGPT analyze deps` for more insights.",
        "",
        SIGNATURE
    ])
    
    return "\n".join(comment_parts)


def _format_no_changes_comment() -> str:
    """Format comment when no dependency changes are detected."""
    return "\n".join([
        "## 📦 Dependency Analysis Results",
        "",
        "✅ **No dependency changes detected in this pull request.**",
        "",
        "This PR doesn't modify any dependency files (requirements.txt, package.json, etc.)",
        "",
        "---",
        "💡 **Need to analyze anyway?** Use `@BlameGPT analyze deps` to force analysis.",
        "",
        SIGNATURE
    ])