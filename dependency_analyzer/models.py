"""
Data models for dependency analysis.

WHAT IT DOES:
- Defines structured data models for dependencies and analysis reports
- Provides type-safe representations of dependency information
- Supports multiple dependency types (runtime, development, peer, optional)
- Enables extensible metadata storage for future enhancements

HOW IT WORKS:
1. **Dependency Model**: Represents a single dependency with name, version, language, type, and metadata
2. **DependencyReport Model**: Aggregates all dependencies with statistics and categorization
3. **Enums**: Define standardized values for dependency types and languages
4. **Auto-calculation**: Report statistics are automatically computed from dependency lists

KEY FEATURES:
- Type safety with dataclasses and enums
- Automatic statistics calculation (counts by language, category, type)
- Extensible metadata system for custom data
- Path handling for cross-platform compatibility
- Query methods for filtering dependencies by various criteria

USAGE:
- Used by parsers to create structured dependency objects
- Used by analyzers to generate comprehensive reports
- Used by exporters to format data for different output formats
- Used by diff analyzers to represent dependency changes
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class DependencyType(Enum):
    """Types of dependencies."""
    RUNTIME = "runtime"
    DEVELOPMENT = "development"
    PEER = "peer"
    OPTIONAL = "optional"
    BUILD = "build"


class Language(Enum):
    """Supported programming languages."""
    PYTHON = "python"
    NODEJS = "nodejs"
    GO = "go"
    RUST = "rust"
    JAVA = "java"
    CSHARP = "csharp"
    RUBY = "ruby"
    PHP = "php"


@dataclass
class Dependency:
    """Represents a single dependency."""
    name: str
    version: str
    language: Language
    dependency_type: DependencyType
    source_file: Path
    category: str | None = None
    description: str | None = None
    homepage: str | None = None
    license: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Ensure source_file is a Path object."""
        if isinstance(self.source_file, str):
            self.source_file = Path(self.source_file)


@dataclass 
class DependencyReport:
    """Complete dependency analysis report."""
    project_name: str
    project_path: Path
    dependencies: list[Dependency]
    total_count: int = 0
    languages: dict[Language, int] = field(default_factory=dict)
    categories: dict[str, int] = field(default_factory=dict)
    dependency_types: dict[DependencyType, int] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Calculate statistics after initialization."""
        self.total_count = len(self.dependencies)
        
        # Count by language
        self.languages = {}
        for dep in self.dependencies:
            self.languages[dep.language] = self.languages.get(dep.language, 0) + 1
            
        # Count by category
        self.categories = {}
        for dep in self.dependencies:
            if dep.category:
                self.categories[dep.category] = self.categories.get(dep.category, 0) + 1
                
        # Count by dependency type
        self.dependency_types = {}
        for dep in self.dependencies:
            self.dependency_types[dep.dependency_type] = self.dependency_types.get(dep.dependency_type, 0) + 1
    
    def get_dependencies_by_language(self, language: Language) -> list[Dependency]:
        """Get all dependencies for a specific language."""
        return [dep for dep in self.dependencies if dep.language == language]
    
    def get_dependencies_by_category(self, category: str) -> list[Dependency]:
        """Get all dependencies for a specific category."""
        return [dep for dep in self.dependencies if dep.category == category]
    
    def get_dependencies_by_type(self, dependency_type: DependencyType) -> list[Dependency]:
        """Get all dependencies of a specific type."""
        return [dep for dep in self.dependencies if dep.dependency_type == dependency_type]