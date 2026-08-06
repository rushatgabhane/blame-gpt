"""
CSV (Comma-Separated Values) exporter for dependency reports.

WHAT IT DOES:
- Exports dependency analysis reports to CSV format
- Creates spreadsheet-compatible tabular data
- Handles proper escaping of special characters
- Sorts data consistently for reproducible output

HOW IT WORKS:
1. **Header Generation**: Creates column headers for all dependency fields
2. **Data Processing**: Converts Dependency objects to flat tabular rows
3. **Path Handling**: Converts absolute paths to relative for portability
4. **CSV Writing**: Uses Python's csv module for proper escaping
5. **Sorting**: Sorts by language then name for consistent output

CSV STRUCTURE:
Columns:
- Dependency Name: Package/library name
- Version: Version specification (1.0.0, ^1.0.0, >=1.0.0, etc.)
- Language: Programming language (python, nodejs, etc.)
- Type: Dependency type (runtime, development, peer, optional)
- Category: Functional category (Web Framework, AI/ML, Testing, etc.)
- Source File: Relative path to dependency file
- Description: Package description (if available)
- Homepage: Package homepage URL (if available)
- License: Package license (if available)

FEATURES:
- Spreadsheet compatibility (Excel, Google Sheets, LibreOffice)
- Proper CSV escaping for commas, quotes, newlines
- Consistent sorting for diff-friendly output
- Relative paths for project portability
- UTF-8 encoding for international characters

USE CASES:
- Data analysis in spreadsheet applications
- Import into business intelligence tools
- Manual review and annotation of dependencies
- Sharing dependency lists with non-technical stakeholders
- Audit trail documentation for compliance

LIMITATIONS:
- Flat structure (no nested data)
- Limited formatting options compared to HTML/Markdown
- No interactive features
- Large files may be unwieldy in some applications
"""

import csv
from pathlib import Path

from ..models import DependencyReport
from .base_exporter import BaseExporter


class CSVExporter(BaseExporter):
    """Export dependency report to CSV format."""
    
    def export(self, report: DependencyReport, output_path: Path) -> None:
        """Export to CSV file."""
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Write header
            writer.writerow([
                'Dependency Name',
                'Version', 
                'Language',
                'Type',
                'Category',
                'Source File',
                'Description',
                'Homepage',
                'License'
            ])
            
            # Write dependency data
            for dep in sorted(report.dependencies, key=lambda x: (x.language.value, x.name.lower())):
                writer.writerow([
                    dep.name,
                    dep.version,
                    dep.language.value,
                    dep.dependency_type.value,
                    dep.category or 'Uncategorized',
                    self._get_relative_path(dep.source_file, report.project_path),
                    dep.description or '',
                    dep.homepage or '',
                    dep.license or ''
                ])
    
    def _get_relative_path(self, file_path: Path, project_path: Path) -> str:
        """Convert absolute path to relative path for portability."""
        try:
            if project_path in file_path.parents:
                return str(file_path.relative_to(project_path))
            else:
                return str(file_path)
        except (ValueError, OSError):
            return str(file_path)