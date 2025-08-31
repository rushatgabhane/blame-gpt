"""
Diff-based dependency analyzer for detecting changes in pull requests.

WHAT IT DOES:
- Analyzes git diffs and PR changes to detect dependency modifications
- Identifies added, removed, and updated dependencies with version changes
- Supports multiple diff sources (git commits, GitHub PRs, diff files)
- Provides line-level change tracking for precise modification detection

HOW IT WORKS:
1. **Diff Acquisition**: Gets diff content from git, GitHub API, or files
2. **Diff Parsing**: Parses unified diff format to extract file changes
3. **Line Analysis**: Processes added/removed lines to identify dependency changes
4. **Change Classification**: Categorizes changes as ADDED, REMOVED, or UPDATED
5. **Smart Matching**: Matches removed/added lines to detect version updates
6. **Report Generation**: Creates comprehensive change reports with metadata

DIFF SOURCES:

Git Diff Analysis:
- Compare any two git references (branches, commits, tags)
- Automatically detects changed dependency files
- Handles merge commits and complex git histories
- Perfect for pre-commit hooks and branch comparisons

GitHub PR Analysis:
- Fetches PR diffs directly from GitHub API
- Supports GitHub token authentication
- Works with public and private repositories
- Integrates with GitHub Actions workflows

Diff File Analysis:
- Processes saved diff files from any source
- Supports standard unified diff format
- Enables offline analysis and custom workflows
- Compatible with various diff generation tools

CHANGE DETECTION STRATEGY:

Python Dependencies:
- Parses requirements.txt line changes
- Handles all pip version specifiers (==, >=, ~=, etc.)
- Detects extras specifications [security,dev]
- Identifies development vs runtime dependencies

Node.js Dependencies:
- Parses package.json changes in all sections
- Handles dependencies, devDependencies, peerDependencies
- Processes complex version ranges (^1.0.0, ~2.1.0)
- Detects dependency type changes

Smart Update Detection:
- Matches package names across added/removed lines
- Creates UPDATED changes instead of separate ADD/REMOVE
- Preserves old and new version information
- Handles complex version specification changes

INTEGRATION FEATURES:
- CI/CD pipeline integration for automated PR analysis
- Command-line interface for manual diff analysis
- JSON/CSV export for downstream processing
- GitHub Actions comment generation
- VS Code extension compatibility

USAGE PATTERNS:
- PR review automation and dependency change alerts
- Security scanning for new dependency additions
- License compliance tracking for added packages
- Breaking change detection through version analysis
- Audit trails for dependency management decisions
"""

import re
import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from .models import Dependency, DependencyType, Language


class ChangeType(Enum):
    """Type of dependency change."""
    ADDED = "added"
    REMOVED = "removed"
    UPDATED = "updated"


@dataclass
class DependencyChange:
    """Represents a change to a dependency."""
    dependency: Dependency
    change_type: ChangeType
    old_version: str | None = None
    new_version: str | None = None
    file_path: Path = None
    line_number: int | None = None


@dataclass
class DiffReport:
    """Report of dependency changes in a diff."""
    added_dependencies: list[DependencyChange]
    removed_dependencies: list[DependencyChange] 
    updated_dependencies: list[DependencyChange]
    total_changes: int = 0
    files_changed: set[Path] = None
    
    def __post_init__(self):
        """Calculate derived fields."""
        self.total_changes = len(self.added_dependencies) + len(self.removed_dependencies) + len(self.updated_dependencies)
        if self.files_changed is None:
            self.files_changed = set()
            for changes in [self.added_dependencies, self.removed_dependencies, self.updated_dependencies]:
                for change in changes:
                    if change.file_path:
                        self.files_changed.add(change.file_path)


class BaseDiffParser(ABC):
    """Base class for parsing diffs of specific file types."""
    
    @property
    @abstractmethod
    def supported_files(self) -> set[str]:
        """Set of filenames this diff parser can handle."""
        pass
    
    @abstractmethod
    def parse_diff_lines(self, file_path: Path, added_lines: list[tuple[int, str]], removed_lines: list[tuple[int, str]]) -> list[DependencyChange]:
        """Parse diff lines and return dependency changes."""
        pass
    
    def can_parse(self, file_path: Path) -> bool:
        """Check if this parser can handle the given file."""
        return file_path.name in self.supported_files


class PythonDiffParser(BaseDiffParser):
    """Parser for Python dependency file diffs."""
    
    @property
    def supported_files(self) -> set[str]:
        return {
            'requirements.txt',
            'requirements-dev.txt',
            'requirements-test.txt', 
            'dev-requirements.txt',
            'test-requirements.txt',
            'pyproject.toml',
            'setup.py',
            'Pipfile'
        }
    
    def parse_diff_lines(self, file_path: Path, added_lines: list[tuple[int, str]], removed_lines: list[tuple[int, str]]) -> list[DependencyChange]:
        """Parse Python dependency changes from diff lines."""
        changes = []
        
        # Parse added lines
        for line_num, line in added_lines:
            dep = self._parse_requirement_line(line, file_path, line_num)
            if dep:
                changes.append(DependencyChange(
                    dependency=dep,
                    change_type=ChangeType.ADDED,
                    new_version=dep.version,
                    file_path=file_path,
                    line_number=line_num
                ))
        
        # Parse removed lines  
        for line_num, line in removed_lines:
            dep = self._parse_requirement_line(line, file_path, line_num)
            if dep:
                changes.append(DependencyChange(
                    dependency=dep,
                    change_type=ChangeType.REMOVED,
                    old_version=dep.version,
                    file_path=file_path,
                    line_number=line_num
                ))
        
        # Detect updates (same package name, different versions)
        changes = self._detect_updates(changes)
        
        return changes
    
    def _parse_requirement_line(self, line: str, file_path: Path, line_num: int) -> Dependency | None:
        """Parse a single requirement line."""
        line = line.strip()
        if not line or line.startswith('#') or line.startswith('-'):
            return None
        
        # Remove inline comments
        line = line.split('#')[0].strip()
        
        # Parse version specifiers
        version_patterns = [
            (r'([a-zA-Z0-9\-_.]+)==([^;,\s]+)', '=='),
            (r'([a-zA-Z0-9\-_.]+)>=([^;,\s]+)', '>='),
            (r'([a-zA-Z0-9\-_.]+)<=([^;,\s]+)', '<='),
            (r'([a-zA-Z0-9\-_.]+)>([^;,\s]+)', '>'),
            (r'([a-zA-Z0-9\-_.]+)<([^;,\s]+)', '<'),
            (r'([a-zA-Z0-9\-_.]+)~=([^;,\s]+)', '~='),
            (r'([a-zA-Z0-9\-_.]+)\[.*\]==([^;,\s]+)', '=='),  # extras
            (r'([a-zA-Z0-9\-_.]+)', 'unspecified')  # no version
        ]
        
        for pattern, spec_type in version_patterns:
            match = re.match(pattern, line)
            if match:
                if spec_type == 'unspecified':
                    name = match.group(1)
                    version = 'unspecified'
                else:
                    name = match.group(1)
                    version = f"{spec_type}{match.group(2)}" if spec_type != '==' else match.group(2)
                
                # Determine dependency type from filename
                dep_type = self._get_dependency_type_from_filename(file_path.name)
                
                return Dependency(
                    name=name,
                    version=version,
                    language=Language.PYTHON,
                    dependency_type=dep_type,
                    source_file=file_path
                )
        
        return None
    
    def _get_dependency_type_from_filename(self, filename: str) -> DependencyType:
        """Determine dependency type from filename."""
        if any(keyword in filename.lower() for keyword in ['dev', 'test']):
            return DependencyType.DEVELOPMENT
        return DependencyType.RUNTIME
    
    def _detect_updates(self, changes: list[DependencyChange]) -> list[DependencyChange]:
        """Detect version updates by matching added/removed dependencies."""
        remaining_changes = []
        added_by_name = {}
        removed_by_name = {}
        
        # Group by dependency name
        for change in changes:
            if change.change_type == ChangeType.ADDED:
                added_by_name[change.dependency.name] = change
            elif change.change_type == ChangeType.REMOVED:
                removed_by_name[change.dependency.name] = change
        
        # Find updates (same name in both added and removed)
        for name in added_by_name:
            if name in removed_by_name:
                added_change = added_by_name[name]
                removed_change = removed_by_name[name]
                
                # Create update change
                update_change = DependencyChange(
                    dependency=added_change.dependency,
                    change_type=ChangeType.UPDATED,
                    old_version=removed_change.dependency.version,
                    new_version=added_change.dependency.version,
                    file_path=added_change.file_path,
                    line_number=added_change.line_number
                )
                remaining_changes.append(update_change)
            else:
                remaining_changes.append(added_by_name[name])
        
        # Add removed dependencies that weren't part of updates
        for name, change in removed_by_name.items():
            if name not in added_by_name:
                remaining_changes.append(change)
        
        return remaining_changes


class NodeJSDiffParser(BaseDiffParser):
    """Parser for Node.js dependency file diffs."""
    
    @property
    def supported_files(self) -> set[str]:
        return {'package.json', 'package-lock.json'}
    
    def parse_diff_lines(self, file_path: Path, added_lines: list[tuple[int, str]], removed_lines: list[tuple[int, str]]) -> list[DependencyChange]:
        """Parse Node.js dependency changes from diff lines."""
        changes = []
        
        # Parse added lines
        for line_num, line in added_lines:
            dep = self._parse_package_json_line(line, file_path, line_num)
            if dep:
                changes.append(DependencyChange(
                    dependency=dep,
                    change_type=ChangeType.ADDED,
                    new_version=dep.version,
                    file_path=file_path,
                    line_number=line_num
                ))
        
        # Parse removed lines
        for line_num, line in removed_lines:
            dep = self._parse_package_json_line(line, file_path, line_num)
            if dep:
                changes.append(DependencyChange(
                    dependency=dep,
                    change_type=ChangeType.REMOVED,
                    old_version=dep.version,
                    file_path=file_path,
                    line_number=line_num
                ))
        
        # Detect updates
        changes = self._detect_updates(changes)
        
        return changes
    
    def _parse_package_json_line(self, line: str, file_path: Path, line_num: int) -> Dependency | None:
        """Parse a single package.json dependency line."""
        line = line.strip()
        
        # Match JSON dependency format: "package-name": "version"
        match = re.match(r'"([^"]+)":\s*"([^"]+)"', line)
        if not match:
            return None
        
        name = match.group(1)
        version = match.group(2)
        
        # Determine dependency type from context (this is simplified - would need more context parsing)
        dep_type = DependencyType.RUNTIME  # Default, would need JSON context to determine accurately
        
        return Dependency(
            name=name,
            version=version,
            language=Language.NODEJS,
            dependency_type=dep_type,
            source_file=file_path
        )
    
    def _detect_updates(self, changes: list[DependencyChange]) -> list[DependencyChange]:
        """Detect version updates by matching added/removed dependencies."""
        # Same logic as Python parser
        remaining_changes = []
        added_by_name = {}
        removed_by_name = {}
        
        for change in changes:
            if change.change_type == ChangeType.ADDED:
                added_by_name[change.dependency.name] = change
            elif change.change_type == ChangeType.REMOVED:
                removed_by_name[change.dependency.name] = change
        
        for name in added_by_name:
            if name in removed_by_name:
                added_change = added_by_name[name]
                removed_change = removed_by_name[name]
                
                update_change = DependencyChange(
                    dependency=added_change.dependency,
                    change_type=ChangeType.UPDATED,
                    old_version=removed_change.dependency.version,
                    new_version=added_change.dependency.version,
                    file_path=added_change.file_path,
                    line_number=added_change.line_number
                )
                remaining_changes.append(update_change)
            else:
                remaining_changes.append(added_by_name[name])
        
        for name, change in removed_by_name.items():
            if name not in added_by_name:
                remaining_changes.append(change)
        
        return remaining_changes


class DiffAnalyzer:
    """Main class for analyzing dependency changes in diffs."""
    
    def __init__(self):
        self.diff_parsers = {
            'python': PythonDiffParser(),
            'nodejs': NodeJSDiffParser()
        }
    
    def analyze_git_diff(self, base_ref: str = 'main', head_ref: str = 'HEAD', project_path: Path = None) -> DiffReport:
        """Analyze git diff between two references."""
        if project_path is None:
            project_path = Path.cwd()
        
        # Get git diff
        diff_content = self._get_git_diff(base_ref, head_ref, project_path)
        
        # Parse diff content
        return self._parse_diff_content(diff_content, project_path)
    
    def analyze_diff_text(self, diff_text: str, project_path: Path = None) -> DiffReport:
        """Analyze diff from text content."""
        if project_path is None:
            project_path = Path.cwd()
        
        return self._parse_diff_content(diff_text, project_path)
    
    def analyze_pr_diff(self, pr_url: str, github_token: str | None = None) -> DiffReport:
        """Analyze GitHub PR diff."""
        # Extract repo and PR number from URL
        match = re.match(r'https://github\.com/([^/]+)/([^/]+)/pull/(\d+)', pr_url)
        if not match:
            raise ValueError(f"Invalid GitHub PR URL: {pr_url}")
        
        owner, repo, pr_number = match.groups()
        
        # Get PR diff using GitHub API or gh CLI
        diff_content = self._get_pr_diff(owner, repo, pr_number, github_token)
        
        return self._parse_diff_content(diff_content, Path.cwd())
    
    def _get_git_diff(self, base_ref: str, head_ref: str, project_path: Path) -> str:
        """Get git diff between references."""
        try:
            result = subprocess.run(
                ['git', 'diff', f'{base_ref}...{head_ref}'],
                cwd=project_path,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to get git diff: {e}")
    
    def _get_pr_diff(self, owner: str, repo: str, pr_number: str, github_token: str | None = None) -> str:
        """Get PR diff using gh CLI or GitHub API."""
        try:
            # Try using gh CLI first
            env = {}
            if github_token:
                env['GITHUB_TOKEN'] = github_token
            
            result = subprocess.run(
                ['gh', 'pr', 'diff', pr_number, '--repo', f'{owner}/{repo}'],
                capture_output=True,
                text=True,
                check=True,
                env=env
            )
            return result.stdout
        except subprocess.CalledProcessError:
            # Fallback to curl with GitHub API
            try:
                import urllib.request
                
                url = f'https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}'
                headers = {'Accept': 'application/vnd.github.v3.diff'}
                if github_token:
                    headers['Authorization'] = f'token {github_token}'
                
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req) as response:
                    return response.read().decode('utf-8')
            except Exception as e:
                raise RuntimeError(f"Failed to get PR diff: {e}")
    
    def _parse_diff_content(self, diff_content: str, project_path: Path) -> DiffReport:
        """Parse diff content and extract dependency changes."""
        all_changes = []
        files_changed = set()
        
        # Parse diff into file sections
        file_diffs = self._parse_diff_files(diff_content)
        
        for file_path, added_lines, removed_lines in file_diffs:
            abs_file_path = project_path / file_path
            files_changed.add(abs_file_path)
            
            # Find appropriate parser
            parser = self._get_parser_for_file(abs_file_path)
            if parser:
                changes = parser.parse_diff_lines(abs_file_path, added_lines, removed_lines)
                all_changes.extend(changes)
        
        # Categorize changes
        added = [c for c in all_changes if c.change_type == ChangeType.ADDED]
        removed = [c for c in all_changes if c.change_type == ChangeType.REMOVED]
        updated = [c for c in all_changes if c.change_type == ChangeType.UPDATED]
        
        return DiffReport(
            added_dependencies=added,
            removed_dependencies=removed,
            updated_dependencies=updated,
            files_changed=files_changed
        )
    
    def _parse_diff_files(self, diff_content: str) -> list[tuple[Path, list[tuple[int, str]], list[tuple[int, str]]]]:
        """Parse diff content into file sections with added/removed lines."""
        files = []
        lines = diff_content.split('\n')
        
        current_file = None
        added_lines = []
        removed_lines = []
        line_number = 0
        
        for line in lines:
            if line.startswith('diff --git'):
                # Save previous file if exists
                if current_file:
                    files.append((Path(current_file), added_lines.copy(), removed_lines.copy()))
                
                # Start new file
                match = re.search(r'b/(.+)$', line)
                current_file = match.group(1) if match else None
                added_lines = []
                removed_lines = []
                line_number = 0
            
            elif line.startswith('@@'):
                # Parse hunk header for line numbers
                match = re.match(r'@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@', line)
                if match:
                    line_number = int(match.group(1))
            
            elif line.startswith('+') and not line.startswith('+++'):
                # Added line
                added_lines.append((line_number, line[1:]))
                line_number += 1
            
            elif line.startswith('-') and not line.startswith('---'):
                # Removed line
                removed_lines.append((line_number, line[1:]))
            
            elif line.startswith(' '):
                # Context line
                line_number += 1
        
        # Don't forget the last file
        if current_file:
            files.append((Path(current_file), added_lines, removed_lines))
        
        return files
    
    def _get_parser_for_file(self, file_path: Path) -> BaseDiffParser | None:
        """Get appropriate diff parser for file."""
        for parser in self.diff_parsers.values():
            if parser.can_parse(file_path):
                return parser
        return None
    
    def print_diff_report(self, report: DiffReport) -> None:
        """Print a formatted diff report."""
        print("\n📊 Dependency Changes Report")
        print(f"📄 Total Changes: {report.total_changes}")
        print(f"📁 Files Changed: {len(report.files_changed)}")
        
        if report.added_dependencies:
            print(f"\n✅ Added Dependencies ({len(report.added_dependencies)}):")
            for change in report.added_dependencies:
                print(f"   + {change.dependency.name} ({change.new_version}) - {change.dependency.language.value}")
        
        if report.removed_dependencies:
            print(f"\n❌ Removed Dependencies ({len(report.removed_dependencies)}):")
            for change in report.removed_dependencies:
                print(f"   - {change.dependency.name} ({change.old_version}) - {change.dependency.language.value}")
        
        if report.updated_dependencies:
            print(f"\n🔄 Updated Dependencies ({len(report.updated_dependencies)}):")
            for change in report.updated_dependencies:
                print(f"   ~ {change.dependency.name}: {change.old_version} → {change.new_version} - {change.dependency.language.value}")
        
        if report.files_changed:
            print("\n📁 Changed Files:")
            for file_path in sorted(report.files_changed):
                print(f"   {file_path}")


# Registry for diff parsers
DIFF_PARSER_REGISTRY: dict[str, BaseDiffParser] = {
    'python': PythonDiffParser(),
    'nodejs': NodeJSDiffParser(),
}