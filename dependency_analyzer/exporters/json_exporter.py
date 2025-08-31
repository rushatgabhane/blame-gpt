"""
JSON exporter for dependency reports.

WHAT IT DOES:
- Exports dependency analysis reports to JSON format
- Creates machine-readable structured data
- Includes comprehensive metadata and statistics
- Provides nested structure with summary and detailed data

HOW IT WORKS:
1. **Data Structuring**: Converts DependencyReport to JSON-serializable dict
2. **Nested Organization**: Creates summary section and detailed dependencies array
3. **Path Normalization**: Converts paths to relative for portability
4. **JSON Serialization**: Uses Python's json module with pretty formatting
5. **UTF-8 Encoding**: Ensures proper encoding for international characters

JSON STRUCTURE:
{
  "project_name": "Project Name",
  "project_path": "/path/to/project",
  "summary": {
    "total_dependencies": 150,
    "languages": {"python": 75, "nodejs": 75},
    "categories": {"Web Framework": 10, "AI/ML": 5, ...},
    "dependency_types": {"runtime": 100, "development": 50}
  },
  "dependencies": [
    {
      "name": "fastapi",
      "version": "0.115.12",
      "language": "python",
      "type": "runtime",
      "category": "Web Framework",
      "source_file": "requirements.txt",
      "description": "FastAPI framework",
      "homepage": "https://fastapi.tiangolo.com",
      "license": "MIT",
      "metadata": {...}
    }
  ],
  "metadata": {...}
}

FEATURES:
- Complete data preservation (all fields included)
- Hierarchical structure for easy navigation
- Machine-readable for API integration
- Pretty-printed for human readability
- Portable paths for cross-platform compatibility
- Comprehensive metadata inclusion

USE CASES:
- API integration and data exchange
- CI/CD pipeline processing and decision making
- Automated security scanning and analysis
- Data warehousing and business intelligence
- Configuration management and infrastructure as code
- Integration with other development tools

ADVANTAGES:
- Preserves all data without loss
- Easy to parse programmatically
- Widely supported across platforms and languages
- Enables complex queries and transformations
- Version control friendly (readable diffs)
"""

import json
from pathlib import Path

from ..models import DependencyReport
from .base_exporter import BaseExporter


class JSONExporter(BaseExporter):
    """Export dependency report to JSON format."""
    
    def export(self, report: DependencyReport, output_path: Path) -> None:
        """Export to JSON file."""
        # Convert report to JSON-serializable format
        json_data = {
            'project_name': report.project_name,
            'project_path': str(report.project_path),
            'summary': {
                'total_dependencies': report.total_count,
                'languages': {lang.value: count for lang, count in report.languages.items()},
                'categories': report.categories,
                'dependency_types': {dep_type.value: count for dep_type, count in report.dependency_types.items()}
            },
            'dependencies': [
                {
                    'name': dep.name,
                    'version': dep.version,
                    'language': dep.language.value,
                    'type': dep.dependency_type.value,
                    'category': dep.category,
                    'source_file': self._get_relative_path(dep.source_file, report.project_path),
                    'description': dep.description,
                    'homepage': dep.homepage,
                    'license': dep.license,
                    'metadata': dep.metadata
                }
                for dep in report.dependencies
            ],
            'metadata': report.metadata
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
    
    def _get_relative_path(self, file_path: Path, project_path: Path) -> str:
        """Convert absolute path to relative path for portability."""
        try:
            if project_path in file_path.parents:
                return str(file_path.relative_to(project_path))
            else:
                return str(file_path)
        except (ValueError, OSError):
            return str(file_path)