"""
Base exporter interface for all export formats.

WHAT IT DOES:
- Defines the standard interface that all exporters must implement
- Ensures consistent export behavior across different formats
- Enables polymorphic usage of different export strategies
- Provides foundation for extensible export system

HOW IT WORKS:
1. **Abstract Interface**: Defines required export method
2. **Report Input**: Takes DependencyReport object with all analysis data
3. **File Output**: Writes formatted data to specified file path
4. **Error Handling**: Consistent error handling patterns

INTERFACE REQUIREMENTS:
- export(report, output_path): Method that writes report to file

IMPLEMENTATION PATTERNS:
- Text-based: CSV, JSON, Markdown (human and machine readable)
- Rich formats: HTML with styling and interactivity
- Structured: JSON for API integration and data processing
- Documentation: Markdown for GitHub/wiki integration

USAGE:
Inherit from BaseExporter to create new export formats:

class XMLExporter(BaseExporter):
    def export(self, report: DependencyReport, output_path: Path) -> None:
        # XML export implementation
        xml_content = self._generate_xml(report)
        with open(output_path, 'w') as f:
            f.write(xml_content)
"""

from abc import ABC, abstractmethod
from pathlib import Path

from ..models import DependencyReport


class BaseExporter(ABC):
    """Base class for all exporters."""
    
    @abstractmethod
    def export(self, report: DependencyReport, output_path: Path) -> None:
        """Export report to specified format."""
        pass