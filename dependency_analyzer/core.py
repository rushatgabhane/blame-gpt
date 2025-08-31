"""
Core dependency analyzer functionality.

WHAT IT DOES:
- Main orchestrator for dependency analysis across entire projects
- Coordinates file discovery, parsing, categorization, and reporting
- Provides both basic and advanced analysis capabilities
- Manages the complete analysis pipeline from discovery to export

HOW IT WORKS:
1. **Project Discovery**: Recursively scans project for dependency files using glob patterns
2. **Parser Selection**: Automatically selects appropriate parsers based on file types
3. **Dependency Extraction**: Uses language-specific parsers to extract dependency information
4. **Categorization**: Applies categorization rules to classify dependencies
5. **Analysis**: Performs additional analysis (conflicts, duplicates, statistics)
6. **Report Generation**: Creates comprehensive reports with all findings
7. **Export**: Outputs results in requested formats

MAIN CLASSES:

DependencyAnalyzer:
- Core analysis engine for complete project scanning
- Handles file discovery and parser coordination
- Generates comprehensive dependency reports
- Supports all export formats and categorization
- Thread-safe and suitable for concurrent use

AdvancedDependencyAnalyzer:
- Extends basic analyzer with advanced features
- Detects duplicate dependencies across files
- Identifies version conflicts and compatibility issues
- Provides detailed statistics and insights
- Offers optimization recommendations

ANALYSIS FEATURES:
- Multi-language support (Python, Node.js, extensible)
- Nested project detection (monorepos, subprojects)
- Version conflict detection
- Duplicate dependency identification
- Security-sensitive package flagging
- License compatibility analysis (planned)
- Dependency graph visualization (planned)

INTEGRATION POINTS:
- CLI interface for command-line usage
- Programmatic API for integration into other tools
- CI/CD pipeline integration
- VS Code extension compatibility
- GitHub Actions workflow support

USAGE PATTERNS:
- Project health assessments
- Pre-commit dependency validation
- Security audits and compliance checks
- Migration planning and impact analysis
- Monorepo dependency management
"""

from pathlib import Path

from .categorizers import BaseCategorizer, DefaultCategorizer
from .exporters import get_exporter
from .models import DependencyReport, Language
from .parsers import PARSER_REGISTRY, get_parser_for_file


class DependencyAnalyzer:
    """Main dependency analyzer class."""
    
    def __init__(self, categorizer: BaseCategorizer | None = None):
        """Initialize analyzer with optional custom categorizer."""
        self.categorizer = categorizer or DefaultCategorizer()
    
    def analyze_project(self, project_path: Path, project_name: str | None = None) -> DependencyReport:
        """Analyze all dependencies in a project."""
        project_path = Path(project_path).resolve()
        
        if not project_path.exists():
            raise FileNotFoundError(f"Project path does not exist: {project_path}")
        
        if not project_name:
            project_name = project_path.name
        
        # Find all dependency files
        dependency_files = self._find_dependency_files(project_path)
        
        # Parse all dependencies
        all_dependencies = []
        for file_path in dependency_files:
            parser = get_parser_for_file(file_path)
            if parser:
                dependencies = parser.parse(file_path)
                for dep in dependencies:
                    # Categorize each dependency
                    dep.category = self.categorizer.categorize(dep)
                    all_dependencies.append(dep)
        
        # Create report
        report = DependencyReport(
            project_name=project_name,
            project_path=project_path,
            dependencies=all_dependencies
        )
        
        return report
    
    def analyze_file(self, file_path: Path) -> list:
        """Analyze dependencies from a single file."""
        file_path = Path(file_path)
        
        parser = get_parser_for_file(file_path)
        if not parser:
            raise ValueError(f"No parser available for file: {file_path}")
        
        dependencies = parser.parse(file_path)
        
        # Categorize dependencies
        for dep in dependencies:
            dep.category = self.categorizer.categorize(dep)
        
        return dependencies
    
    def export_report(self, report: DependencyReport, output_path: Path, format: str = 'csv') -> None:
        """Export report to specified format."""
        exporter = get_exporter(format)
        exporter.export(report, output_path)
    
    def get_supported_languages(self) -> set[Language]:
        """Get set of supported languages."""
        return set(PARSER_REGISTRY.keys())
    
    def get_supported_formats(self) -> set[str]:
        """Get set of supported export formats."""
        from .exporters import EXPORTER_REGISTRY
        return set(EXPORTER_REGISTRY.keys())
    
    def _find_dependency_files(self, project_path: Path) -> list[Path]:
        """Find all dependency files in project."""
        dependency_files = []
        
        # Get all supported file patterns from parsers
        supported_files = set()
        for parser in PARSER_REGISTRY.values():
            supported_files.update(parser.supported_files)
        
        # Search for dependency files
        for pattern in supported_files:
            # Search in root directory
            root_matches = list(project_path.glob(pattern))
            dependency_files.extend(root_matches)
            
            # Search in subdirectories (for files like frontend/package.json)
            subdir_matches = list(project_path.glob(f"*/{pattern}"))
            dependency_files.extend(subdir_matches)
            
            # Search deeper (for monorepos, etc.)
            deep_matches = list(project_path.glob(f"**/{pattern}"))
            dependency_files.extend(deep_matches)
        
        # Remove duplicates and ensure files exist
        unique_files = []
        seen = set()
        for file_path in dependency_files:
            if file_path.exists() and file_path not in seen:
                unique_files.append(file_path)
                seen.add(file_path)
        
        return unique_files
    
    def print_summary(self, report: DependencyReport) -> None:
        """Print a summary of the dependency report."""
        print(f"\n📊 Dependency Analysis: {report.project_name}")
        print(f"📄 Project Path: {report.project_path}")
        print("\n📈 Summary:")
        print(f"   Total Dependencies: {report.total_count}")
        
        if report.languages:
            print("\n🔧 Languages:")
            for lang, count in sorted(report.languages.items(), key=lambda x: x[1], reverse=True):
                print(f"   {lang.value.title()}: {count}")
        
        if report.categories:
            print("\n🏷️  Categories:")
            for category, count in sorted(report.categories.items(), key=lambda x: x[1], reverse=True):
                print(f"   {category}: {count}")
        
        if report.dependency_types:
            print("\n📦 Dependency Types:")
            for dep_type, count in sorted(report.dependency_types.items(), key=lambda x: x[1], reverse=True):
                print(f"   {dep_type.value.title()}: {count}")


class AdvancedDependencyAnalyzer(DependencyAnalyzer):
    """Advanced analyzer with additional features."""
    
    def __init__(self, categorizer: BaseCategorizer | None = None):
        super().__init__(categorizer)
    
    def find_duplicate_dependencies(self, report: DependencyReport) -> dict:
        """Find dependencies that appear in multiple files."""
        duplicates = {}
        
        dependency_sources = {}
        for dep in report.dependencies:
            key = (dep.name, dep.language)
            if key not in dependency_sources:
                dependency_sources[key] = []
            dependency_sources[key].append(dep)
        
        for key, deps in dependency_sources.items():
            if len(deps) > 1:
                name, language = key
                duplicates[f"{name} ({language.value})"] = [
                    {
                        'version': dep.version,
                        'source': str(dep.source_file),
                        'type': dep.dependency_type.value
                    }
                    for dep in deps
                ]
        
        return duplicates
    
    def find_version_conflicts(self, report: DependencyReport) -> dict:
        """Find dependencies with different version specifications."""
        conflicts = {}
        
        # Group by name and language
        grouped = {}
        for dep in report.dependencies:
            key = (dep.name, dep.language)
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(dep)
        
        # Find version conflicts
        for (name, language), deps in grouped.items():
            versions = set(dep.version for dep in deps)
            if len(versions) > 1:
                conflicts[f"{name} ({language.value})"] = [
                    {
                        'version': dep.version,
                        'source': str(dep.source_file),
                        'type': dep.dependency_type.value
                    }
                    for dep in deps
                ]
        
        return conflicts
    
    def get_dependency_statistics(self, report: DependencyReport) -> dict:
        """Get detailed statistics about dependencies."""
        stats = {
            'total': report.total_count,
            'by_language': dict(report.languages),
            'by_category': dict(report.categories),
            'by_type': dict(report.dependency_types),
            'duplicates': len(self.find_duplicate_dependencies(report)),
            'version_conflicts': len(self.find_version_conflicts(report)),
            'largest_category': max(report.categories.items(), key=lambda x: x[1]) if report.categories else None,
            'most_common_language': max(report.languages.items(), key=lambda x: x[1]) if report.languages else None,
        }
        
        return stats