"""
Base categorizer interface for all dependency categorization strategies.

WHAT IT DOES:
- Defines the standard interface that all categorizers must implement
- Ensures consistent categorization behavior across different strategies
- Enables polymorphic usage of different categorization approaches
- Provides foundation for extensible categorization system

HOW IT WORKS:
1. **Abstract Interface**: Defines required categorize method
2. **Dependency Input**: Takes Dependency object with metadata
3. **Category Output**: Returns string category name
4. **Extensibility**: Easy to implement custom categorization logic

INTERFACE REQUIREMENTS:
- categorize(dependency): Method that returns category string for a dependency

IMPLEMENTATION PATTERNS:
- Rule-based: Pattern matching on dependency names
- Machine Learning: Trained models for classification
- Hybrid: Combination of rules and ML
- Custom: User-defined business logic

USAGE:
Inherit from BaseCategorizer to create new categorization strategies:

class DomainCategorizer(BaseCategorizer):
    def categorize(self, dependency: Dependency) -> str:
        # Custom categorization logic
        if dependency.name in self.security_packages:
            return "Security"
        return "Other"
"""

from abc import ABC, abstractmethod

from ..models import Dependency


class BaseCategorizer(ABC):
    """Base class for all dependency categorizers."""
    
    @abstractmethod
    def categorize(self, dependency: Dependency) -> str:
        """Categorize a dependency and return category name."""
        pass