"""
Markdown exporter for dependency reports.

WHAT IT DOES:
- Exports dependency analysis reports to Markdown format
- Creates structured documentation suitable for README files and wikis
- Generates hierarchical content with summary statistics
- Provides easy-to-read tabular dependency listings by language

HOW IT WORKS:
1. **Header Generation**: Creates main heading with project name
2. **Summary Section**: Provides high-level statistics and breakdowns
3. **Language Sections**: Organizes dependencies by programming language
4. **Table Generation**: Creates markdown tables for each language's dependencies
5. **Path Normalization**: Converts paths to relative for portability

MARKDOWN STRUCTURE:
# Dependency Report: Project Name

## Summary
- **Total Dependencies**: 150
- **Project Path**: `/path/to/project`

### Languages
- **Python**: 75 dependencies
- **Nodejs**: 75 dependencies

### Categories
- **Web Framework**: 10 dependencies
- **AI/ML**: 5 dependencies

### Dependency Types
- **Runtime**: 100 dependencies
- **Development**: 50 dependencies

## Python Dependencies
| Name | Version | Type | Category | Source |
|------|---------|------|----------|--------|
| fastapi | 0.115.12 | runtime | Web Framework | requirements.txt |

FEATURES:
- GitHub/GitLab compatible markdown syntax
- Hierarchical structure for easy navigation
- Sortable tables with proper alignment
- Relative paths for project portability
- Comprehensive statistical breakdown
- Language-specific dependency grouping

USE CASES:
- README file integration for project documentation
- Wiki pages for team knowledge sharing
- Pull request descriptions with dependency changes
- Architecture documentation and dependency mapping
- Code review supporting documentation
- Project onboarding materials

ADVANTAGES:
- Highly readable in both raw and rendered form
- Version control friendly (clean diffs)
- Widely supported across platforms (GitHub, GitLab, etc.)
- Easy to edit manually if needed
- Integrates well with existing markdown documentation
"""

from pathlib import Path

from ..models import DependencyReport
from .base_exporter import BaseExporter


class MarkdownExporter(BaseExporter):
    """Export dependency report to Markdown format."""
    
    def export(self, report: DependencyReport, output_path: Path) -> None:
        """Export to Markdown file."""
        with open(output_path, 'w', encoding='utf-8') as f:
            # Write header
            f.write(f"# Dependency Report: {report.project_name}\n\n")
            
            # Write summary
            f.write("## Summary\n\n")
            f.write(f"- **Total Dependencies**: {report.total_count}\n")
            f.write(f"- **Project Path**: `{report.project_path}`\n\n")
            
            # Languages breakdown
            if report.languages:
                f.write("### Languages\n\n")
                for lang, count in sorted(report.languages.items(), key=lambda x: x[1], reverse=True):
                    f.write(f"- **{lang.value.title()}**: {count} dependencies\n")
                f.write("\n")
            
            # Categories breakdown
            if report.categories:
                f.write("### Categories\n\n")
                for category, count in sorted(report.categories.items(), key=lambda x: x[1], reverse=True):
                    f.write(f"- **{category}**: {count} dependencies\n")
                f.write("\n")
            
            # Dependency types breakdown
            if report.dependency_types:
                f.write("### Dependency Types\n\n")
                for dep_type, count in sorted(report.dependency_types.items(), key=lambda x: x[1], reverse=True):
                    f.write(f"- **{dep_type.value.title()}**: {count} dependencies\n")
                f.write("\n")
            
            # Dependencies by language
            for language in sorted(report.languages.keys(), key=lambda x: x.value):
                deps = report.get_dependencies_by_language(language)
                if deps:
                    f.write(f"## {language.value.title()} Dependencies\n\n")
                    f.write("| Name | Version | Type | Category | Source |\n")
                    f.write("|------|---------|------|----------|--------|\n")
                    
                    for dep in sorted(deps, key=lambda x: x.name.lower()):
                        source_file = self._get_relative_path(dep.source_file, report.project_path)
                        f.write(f"| {dep.name} | {dep.version} | {dep.dependency_type.value} | {dep.category or 'Uncategorized'} | {source_file} |\n")
                    f.write("\n")
    
    def _get_relative_path(self, file_path: Path, project_path: Path) -> str:
        """Convert absolute path to relative path for portability."""
        try:
            if project_path in file_path.parents:
                return str(file_path.relative_to(project_path))
            else:
                return str(file_path)
        except (ValueError, OSError):
            return str(file_path)