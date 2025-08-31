"""
Dependency categorization system package.

WHAT IT DOES:
- Provides automatic dependency categorization into functional groups
- Supports multiple categorization strategies (rule-based, custom, ML)
- Enables easy extension with new categorization logic
- Maintains consistent categorization interface

HOW IT WORKS:
- Default categorizer uses rule-based pattern matching
- Custom categorizer allows user-defined rules
- ML categorizer provides foundation for machine learning approaches
- Registry system enables categorizer selection and extension

USAGE:
from dependency_analyzer.categorizers import DefaultCategorizer, CustomCategorizer
"""

from .base_categorizer import BaseCategorizer
from .custom_categorizer import CustomCategorizer
from .default_categorizer import DefaultCategorizer
from .ml_categorizer import MLCategorizer

__all__ = [
    'BaseCategorizer',
    'DefaultCategorizer',
    'CustomCategorizer', 
    'MLCategorizer'
]