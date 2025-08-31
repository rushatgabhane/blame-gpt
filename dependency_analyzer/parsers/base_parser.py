"""
Base parser interface for all language-specific parsers.

WHAT IT DOES:
- Defines the common interface that all language parsers must implement
- Provides shared utilities for file handling and validation
- Ensures consistent behavior across different language parsers
- Enables polymorphic usage of parsers through common interface

HOW IT WORKS:
1. **Abstract Interface**: Defines required methods (language, supported_files, parse)
2. **File Detection**: Common can_parse method checks file compatibility
3. **Error Handling**: Consistent error handling patterns
4. **Extensibility**: Easy to inherit and extend for new languages

INTERFACE REQUIREMENTS:
- language: Property returning the Language enum for this parser
- supported_files: Set of filenames this parser can handle
- parse: Method to extract dependencies from a file

USAGE:
Inherit from BaseParser to create new language parsers:

class GoParser(BaseParser):
    @property
    def language(self) -> Language:
        return Language.GO
    
    @property
    def supported_files(self) -> Set[str]:
        return {'go.mod', 'go.sum'}
    
    def parse(self, file_path: Path) -> List[Dependency]:
        # Implementation here
        pass
"""

from abc import ABC, abstractmethod
from pathlib import Path

from ..models import Dependency, Language


class BaseParser(ABC):
    """Base class for all dependency parsers."""
    
    @property
    @abstractmethod
    def language(self) -> Language:
        """The language this parser handles."""
        pass
    
    @property
    @abstractmethod
    def supported_files(self) -> set[str]:
        """Set of filenames this parser can handle."""
        pass
    
    @abstractmethod
    def parse(self, file_path: Path) -> list[Dependency]:
        """Parse dependencies from a file."""
        pass
    
    def can_parse(self, file_path: Path) -> bool:
        """Check if this parser can handle the given file."""
        return file_path.name in self.supported_files and file_path.exists()
    
    def _validate_file(self, file_path: Path) -> None:
        """Validate that file can be processed."""
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if not self.can_parse(file_path):
            raise ValueError(f"Parser cannot handle file: {file_path.name}")
    
    def _handle_parse_error(self, file_path: Path, error: Exception) -> list[Dependency]:
        """Handle parsing errors consistently."""
        print(f"Warning: Error parsing {file_path}: {error}")
        return []