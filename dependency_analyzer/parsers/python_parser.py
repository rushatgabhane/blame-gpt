"""
Python dependency parser for requirements.txt and related files.

WHAT IT DOES:
- Parses Python dependency files (requirements.txt, pyproject.toml, etc.)
- Extracts dependency names, versions, and specification types
- Handles different Python package formats and version specifiers
- Automatically detects development vs runtime dependencies

HOW IT WORKS:
1. **File Type Detection**: Identifies Python dependency files by name
2. **Line-by-line Parsing**: Processes each line for dependency information
3. **Regex Matching**: Uses patterns to extract package names and versions
4. **Type Classification**: Determines dependency type from filename
5. **Object Creation**: Returns structured Dependency objects

SUPPORTED FILES:
- requirements.txt (standard pip requirements)
- requirements-dev.txt, requirements-test.txt (development dependencies)
- dev-requirements.txt, test-requirements.txt (alternative naming)
- pyproject.toml, setup.py, Pipfile (planned - currently returns empty)

VERSION SPECIFICATIONS:
- Exact: package==1.0.0
- Minimum: package>=1.0.0
- Maximum: package<=1.0.0
- Compatible: package~=1.0.0
- Range: package>=1.0.0,<2.0.0
- Extras: package[extra]==1.0.0
- No version: package (unspecified)

DEPENDENCY TYPE DETECTION:
- Files with 'dev' or 'test' in name → DependencyType.DEVELOPMENT
- All other files → DependencyType.RUNTIME

FUTURE ENHANCEMENTS:
- pyproject.toml parsing with TOML library
- setup.py parsing with AST analysis
- Pipfile parsing for Pipenv projects
- Poetry.lock parsing for Poetry projects
"""

import re
from pathlib import Path

from ..models import Dependency, DependencyType, Language
from .base_parser import BaseParser


class PythonParser(BaseParser):
    """Parser for Python dependency files."""
    
    @property
    def language(self) -> Language:
        return Language.PYTHON
    
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
            'Pipfile',
            'poetry.lock'
        }
    
    def parse(self, file_path: Path) -> list[Dependency]:
        """Parse Python dependencies from various file formats."""
        try:
            self._validate_file(file_path)
            
            if file_path.name.endswith('.txt'):
                return self._parse_requirements_txt(file_path)
            elif file_path.name == 'pyproject.toml':
                return self._parse_pyproject_toml(file_path)
            elif file_path.name == 'setup.py':
                return self._parse_setup_py(file_path)
            elif file_path.name == 'Pipfile':
                return self._parse_pipfile(file_path)
            else:
                return []
                
        except Exception as e:
            return self._handle_parse_error(file_path, e)
    
    def _parse_requirements_txt(self, file_path: Path) -> list[Dependency]:
        """Parse requirements.txt format."""
        dependencies = []
        
        # Determine dependency type from filename
        dep_type = self._get_dependency_type_from_filename(file_path.name)
        
        try:
            with open(file_path, encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line or line.startswith('#') or line.startswith('-'):
                        continue
                    
                    # Parse different requirement formats
                    dep = self._parse_requirement_line(line, file_path, dep_type)
                    if dep:
                        dependencies.append(dep)
                        
        except Exception as e:
            return self._handle_parse_error(file_path, e)
        
        return dependencies
    
    def _parse_requirement_line(self, line: str, file_path: Path, dep_type: DependencyType) -> Dependency | None:
        """Parse a single requirement line."""
        # Remove inline comments
        line = line.split('#')[0].strip()
        
        # Handle different version specifiers
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
                
                return Dependency(
                    name=name,
                    version=version,
                    language=self.language,
                    dependency_type=dep_type,
                    source_file=file_path
                )
        
        return None
    
    def _get_dependency_type_from_filename(self, filename: str) -> DependencyType:
        """Determine dependency type from filename."""
        if any(keyword in filename.lower() for keyword in ['dev', 'test']):
            return DependencyType.DEVELOPMENT
        return DependencyType.RUNTIME
    
    def _parse_pyproject_toml(self, file_path: Path) -> list[Dependency]:
        """Parse pyproject.toml dependencies."""
        # TODO: Implement TOML parsing - requires toml library
        print(f"Info: pyproject.toml parsing not yet implemented for {file_path}")
        return []
    
    def _parse_setup_py(self, file_path: Path) -> list[Dependency]:
        """Parse setup.py dependencies."""
        # TODO: Implement setup.py parsing - requires AST parsing
        print(f"Info: setup.py parsing not yet implemented for {file_path}")
        return []
    
    def _parse_pipfile(self, file_path: Path) -> list[Dependency]:
        """Parse Pipfile dependencies."""
        # TODO: Implement Pipfile parsing - requires toml library  
        print(f"Info: Pipfile parsing not yet implemented for {file_path}")
        return []