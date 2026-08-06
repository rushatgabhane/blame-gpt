"""
Dependency report exporters package.

WHAT IT DOES:
- Provides export functionality for dependency analysis reports
- Supports multiple output formats (CSV, JSON, HTML, Markdown)
- Enables easy addition of new export formats
- Maintains consistent export interface across formats

HOW IT WORKS:
- Each format has its own exporter module
- Registry system maps format names to exporter classes
- Factory function provides easy exporter access
- Base exporter defines common interface

USAGE:
from dependency_analyzer.exporters import get_exporter, CSVExporter
"""

from .base_exporter import BaseExporter
from .csv_exporter import CSVExporter
from .html_exporter import HTMLExporter
from .json_exporter import JSONExporter
from .markdown_exporter import MarkdownExporter

# Export format registry
EXPORTER_REGISTRY = {
    'csv': CSVExporter(),
    'json': JSONExporter(), 
    'md': MarkdownExporter(),
    'html': HTMLExporter(),
}

def get_exporter(format_name: str) -> BaseExporter:
    """Get exporter for specified format."""
    if format_name not in EXPORTER_REGISTRY:
        raise ValueError(f"Unsupported export format: {format_name}")
    return EXPORTER_REGISTRY[format_name]

__all__ = [
    'BaseExporter',
    'CSVExporter',
    'JSONExporter',
    'MarkdownExporter', 
    'HTMLExporter',
    'get_exporter',
    'EXPORTER_REGISTRY'
]