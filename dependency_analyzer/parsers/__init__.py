"""
Language-specific dependency parsers package.

WHAT IT DOES:
- Provides parsers for different programming language dependency files
- Centralizes parser registration and discovery
- Enables easy addition of new language support
- Maintains consistent parsing interface across languages

HOW IT WORKS:
- Each language has its own parser module (python_parser.py, nodejs_parser.py)
- Base parser defines common interface and utilities
- Registry system enables automatic parser discovery
- Factory functions provide easy parser access

USAGE:
from dependency_analyzer.parsers import get_parser_for_file, PythonParser
"""

from .base_parser import BaseParser
from .nodejs_parser import NodeJSParser
from .python_parser import PythonParser

# Parser registry for dynamic discovery
PARSER_REGISTRY = {
    'python': PythonParser(),
    'nodejs': NodeJSParser(),
}

def get_parser_for_language(language_name: str):
    """Get parser for a specific language."""
    return PARSER_REGISTRY.get(language_name.lower())

def get_parser_for_file(file_path):
    """Get appropriate parser for a file."""
    from pathlib import Path
    file_path = Path(file_path)
    
    for parser in PARSER_REGISTRY.values():
        if parser.can_parse(file_path):
            return parser
    return None

__all__ = [
    'BaseParser',
    'PythonParser', 
    'NodeJSParser',
    'get_parser_for_language',
    'get_parser_for_file',
    'PARSER_REGISTRY'
]