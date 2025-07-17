"""
PR analysis and dependency resolution components.
"""

from .dependency_resolver import DependencyResolver
from .pr_diff_analyzer import PRDiffAnalyzer

__all__ = [
    "PRDiffAnalyzer",
    "DependencyResolver"
]