"""
Dependency Analyzer - A extensible module for analyzing project dependencies across multiple languages.

WHAT IT DOES:
- Analyzes project dependencies across Python and Node.js (extensible to other languages)
- Detects dependency changes in PR diffs and git commits
- Categorizes dependencies by type (web framework, AI/ML, database, etc.)
- Exports analysis results in multiple formats (CSV, JSON, HTML, Markdown)
- Identifies version conflicts, duplicates, and security-sensitive packages

HOW IT WORKS:
1. **Discovery Phase**: Recursively finds dependency files (requirements.txt, package.json, etc.)
2. **Parsing Phase**: Language-specific parsers extract dependencies with version info
3. **Analysis Phase**: Categorizes dependencies and detects conflicts/duplicates
4. **Export Phase**: Generates reports in requested formats
5. **Diff Mode**: Compares git diffs to detect added/removed/updated dependencies

MAIN COMPONENTS:
- DependencyAnalyzer: Core analyzer for full project analysis
- AdvancedDependencyAnalyzer: Extended analyzer with conflict detection
- DiffAnalyzer: Specialized analyzer for PR/commit diff analysis
- Parsers: Language-specific dependency file parsers (Python, Node.js)
- Exporters: Multi-format report generators (CSV, JSON, HTML, MD)
- Categorizers: Smart dependency classification system

USE CASES:
- CI/CD pipeline dependency monitoring
- PR review automation for dependency changes
- Security audits and license compliance
- Project health assessments and optimization
- Monorepo dependency management

Supports Python, Node.js, and can be easily extended for other languages like Go, Rust, Java, etc.
"""

from .categorizers import DefaultCategorizer
from .core import AdvancedDependencyAnalyzer, DependencyAnalyzer
from .diff_analyzer import ChangeType, DependencyChange, DiffAnalyzer, DiffReport
from .exporters import CSVExporter, JSONExporter
from .models import Dependency, DependencyReport
from .parsers import NodeJSParser, PythonParser

__version__ = "1.0.0"
__all__ = [
    "DependencyAnalyzer",
    "AdvancedDependencyAnalyzer", 
    "Dependency", 
    "DependencyReport",
    "PythonParser",
    "NodeJSParser", 
    "CSVExporter",
    "JSONExporter",
    "DefaultCategorizer",
    "DiffAnalyzer",
    "DependencyChange",
    "DiffReport",
    "ChangeType"
]