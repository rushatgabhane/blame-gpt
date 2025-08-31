"""
Custom user-defined dependency categorizer.

WHAT IT DOES:
- Allows users to define their own categorization rules
- Supports custom business logic and domain-specific categories
- Provides fallback to default categorizer for unmatched dependencies
- Enables organization-specific dependency classification

HOW IT WORKS:
1. **Custom Rules**: User provides dictionary of category → patterns mapping
2. **Pattern Matching**: Uses simple string contains matching
3. **Priority Logic**: Custom rules take precedence over default rules
4. **Fallback**: Unmatched dependencies use DefaultCategorizer

USAGE EXAMPLES:

# Security-focused categorization
security_rules = {
    "High Security": ["openssl", "cryptography", "bcrypt", "jwt"],
    "Auth Systems": ["passport", "oauth", "saml", "ldap"],
    "Compliance": ["audit", "gdpr", "hipaa", "sox"]
}
categorizer = CustomCategorizer(security_rules)

# Domain-specific categorization  
ml_rules = {
    "Deep Learning": ["torch", "tensorflow", "keras", "pytorch"],
    "Data Science": ["pandas", "numpy", "scikit", "matplotlib"],
    "NLP": ["nltk", "spacy", "transformers", "langchain"],
    "Computer Vision": ["opencv", "pillow", "skimage", "torchvision"]
}
categorizer = CustomCategorizer(ml_rules)

# Company-specific categorization
company_rules = {
    "Internal Tools": ["company-utils", "internal-auth", "corp-logger"],
    "Legacy Systems": ["old-framework", "deprecated-lib", "legacy-api"],
    "Approved Libraries": ["approved-http", "company-standards"]
}
categorizer = CustomCategorizer(company_rules)

EXTENSIBILITY:
- Easy to modify rules at runtime
- Can be combined with other categorizers
- Supports regex patterns (with future enhancement)
- Enables A/B testing of categorization strategies
"""


from ..models import Dependency
from .base_categorizer import BaseCategorizer
from .default_categorizer import DefaultCategorizer


class CustomCategorizer(BaseCategorizer):
    """User-defined custom categorizer."""
    
    def __init__(self, custom_rules: dict[str, list[str]]):
        """
        Initialize with custom categorization rules.
        
        Args:
            custom_rules: Dictionary mapping category names to lists of patterns
                         e.g., {"Security": ["crypto", "jwt"], "ML": ["torch", "sklearn"]}
        """
        self.custom_rules = custom_rules
        self.fallback_categorizer = DefaultCategorizer()
    
    def categorize(self, dependency: Dependency) -> str:
        """Categorize using custom user-defined rules."""
        name_lower = dependency.name.lower()
        
        # Check custom rules first
        for category, patterns in self.custom_rules.items():
            for pattern in patterns:
                if pattern.lower() in name_lower:
                    return category
        
        # Fallback to default categorizer
        return self.fallback_categorizer.categorize(dependency)
    
    def add_rule(self, category: str, patterns: list[str]) -> None:
        """Add new categorization rule."""
        if category in self.custom_rules:
            self.custom_rules[category].extend(patterns)
        else:
            self.custom_rules[category] = patterns.copy()
    
    def remove_rule(self, category: str) -> None:
        """Remove categorization rule."""
        if category in self.custom_rules:
            del self.custom_rules[category]
    
    def update_rule(self, category: str, patterns: list[str]) -> None:
        """Update existing categorization rule."""
        self.custom_rules[category] = patterns.copy()
    
    def get_rules(self) -> dict[str, list[str]]:
        """Get copy of current rules."""
        return {cat: patterns.copy() for cat, patterns in self.custom_rules.items()}