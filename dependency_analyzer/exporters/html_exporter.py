"""
HTML exporter for dependency reports.

WHAT IT DOES:
- Exports dependency analysis reports to HTML format
- Creates interactive, styled web pages for dependency visualization
- Provides responsive design with modern CSS styling
- Generates standalone HTML files with embedded CSS

HOW IT WORKS:
1. **HTML Generation**: Creates complete HTML document structure
2. **CSS Styling**: Embeds modern CSS for professional appearance
3. **Responsive Layout**: Uses CSS Grid for adaptive layout
4. **Data Visualization**: Presents statistics in visually appealing cards
5. **Table Generation**: Creates styled tables for dependency listings
6. **Path Normalization**: Converts paths to relative for portability

HTML STRUCTURE:
<!DOCTYPE html>
<html>
<head>
  <title>Dependency Report: Project Name</title>
  <style>/* Embedded CSS styling */</style>
</head>
<body>
  <div class="header">
    <h1>📦 Dependency Report: Project Name</h1>
    <p>Project Path: /path/to/project</p>
  </div>
  
  <div class="summary">
    <div class="stat-card">Total Dependencies: 150</div>
    <div class="stat-card">Languages: 2</div>
    <div class="stat-card">Categories: 5</div>
  </div>
  
  <div class="language-section">
    <h2>🔧 Python Dependencies (75)</h2>
    <table>...</table>
  </div>
</body>
</html>

FEATURES:
- Professional styling with modern design patterns
- Responsive layout that works on all screen sizes
- Interactive elements with hover effects
- Semantic HTML structure for accessibility
- Standalone files (no external dependencies)
- Visual hierarchy with cards and sections
- Color-coded elements for better organization

USE CASES:
- Web-based dependency dashboards
- Stakeholder presentations and reports
- Documentation websites and portals
- Team wiki integration
- Executive summaries with visual appeal
- Compliance and audit reporting
- Integration into existing web applications

ADVANTAGES:
- Rich visual presentation with styling
- Interactive and user-friendly interface
- Printable format for offline documentation
- Shareable via web hosting or email
- Professional appearance for stakeholder presentations
- Embedded CSS means no external dependencies
"""

from pathlib import Path

from ..models import Dependency, DependencyReport
from .base_exporter import BaseExporter


class HTMLExporter(BaseExporter):
    """Export dependency report to HTML format."""
    
    def export(self, report: DependencyReport, output_path: Path) -> None:
        """Export to HTML file."""
        html_content = self._generate_html(report)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    def _generate_html(self, report: DependencyReport) -> str:
        """Generate HTML content for the report."""
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dependency Report: {report.project_name}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 40px; }}
        .header {{ background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 30px; }}
        .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .stat-card {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .stat-card h3 {{ margin: 0 0 10px 0; color: #495057; }}
        .stat-card .number {{ font-size: 2em; font-weight: bold; color: #007bff; }}
        table {{ width: 100%; border-collapse: collapse; margin-bottom: 30px; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #dee2e6; }}
        th {{ background-color: #f8f9fa; font-weight: 600; }}
        .language-section {{ margin-bottom: 40px; }}
        .badge {{ display: inline-block; padding: 4px 8px; background: #e9ecef; border-radius: 4px; font-size: 0.85em; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📦 Dependency Report: {report.project_name}</h1>
        <p><strong>Project Path:</strong> <code>{report.project_path}</code></p>
    </div>
    
    <div class="summary">
        <div class="stat-card">
            <h3>Total Dependencies</h3>
            <div class="number">{report.total_count}</div>
        </div>
        <div class="stat-card">
            <h3>Languages</h3>
            <div class="number">{len(report.languages)}</div>
        </div>
        <div class="stat-card">
            <h3>Categories</h3>
            <div class="number">{len(report.categories)}</div>
        </div>
    </div>
    
    {self._generate_language_sections(report)}
</body>
</html>
"""
    
    def _generate_language_sections(self, report: DependencyReport) -> str:
        """Generate HTML sections for each language."""
        sections = []
        
        for language in sorted(report.languages.keys(), key=lambda x: x.value):
            deps = report.get_dependencies_by_language(language)
            if deps:
                sections.append(f"""
    <div class="language-section">
        <h2>🔧 {language.value.title()} Dependencies ({len(deps)})</h2>
        <table>
            <thead>
                <tr>
                    <th>Name</th>
                    <th>Version</th>
                    <th>Type</th>
                    <th>Category</th>
                    <th>Source</th>
                </tr>
            </thead>
            <tbody>
                {self._generate_table_rows(deps, report.project_path)}
            </tbody>
        </table>
    </div>
                """)
        
        return ''.join(sections)
    
    def _generate_table_rows(self, dependencies: list[Dependency], project_path: Path) -> str:
        """Generate HTML table rows for dependencies."""
        rows = []
        
        for dep in sorted(dependencies, key=lambda x: x.name.lower()):
            source_file = self._get_relative_path(dep.source_file, project_path)
            rows.append(f"""
                <tr>
                    <td><strong>{dep.name}</strong></td>
                    <td><code>{dep.version}</code></td>
                    <td><span class="badge">{dep.dependency_type.value}</span></td>
                    <td>{dep.category or 'Uncategorized'}</td>
                    <td><code>{source_file}</code></td>
                </tr>
            """)
        
        return ''.join(rows)
    
    def _get_relative_path(self, file_path: Path, project_path: Path) -> str:
        """Convert absolute path to relative path for portability."""
        try:
            if project_path in file_path.parents:
                return str(file_path.relative_to(project_path))
            else:
                return str(file_path)
        except (ValueError, OSError):
            return str(file_path)