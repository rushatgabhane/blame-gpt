"""
TreeSitter-based code parsing service.

This module will use TreeSitter to parse source code and extract:
- Functions and methods
- Classes and interfaces  
- Variables and constants
- Import statements
- Call relationships
- Inheritance relationships

Note: TreeSitter dependencies need to be installed for full functionality.
For now, this includes basic regex-based parsing as a fallback.
"""

import re
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ParsedNode:
    """Represents a parsed code element."""
    node_type: str  # 'function', 'class', 'method', 'variable', 'import'
    name: str
    full_name: Optional[str] = None
    signature: Optional[str] = None
    start_line: Optional[int] = None
    end_line: Optional[int] = None
    content: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass  
class ParsedRelationship:
    """Represents a relationship between code elements."""
    source_name: str
    target_name: str
    relationship_type: str  # 'calls', 'imports', 'inherits', 'contains'
    metadata: Optional[Dict[str, Any]] = None


class TreeSitterParser:
    """TreeSitter-based code parser with regex fallback."""
    
    def __init__(self):
        self.parsers = {}
        self._setup_parsers()
    
    def _setup_parsers(self):
        """Initialize TreeSitter parsers for different languages."""
        try:
            # Try to import TreeSitter
            from tree_sitter import Language, Parser
            from tree_sitter_typescript import language_tsx, language_typescript
            
            # Setup TypeScript/TSX parsers
            self.parsers['typescript'] = Parser(Language(language_typescript()))
            self.parsers['tsx'] = Parser(Language(language_tsx()))
            
            logger.info("TreeSitter parsers initialized successfully")
            
        except ImportError:
            logger.warning("TreeSitter not available, using regex fallback parsing")
            self.parsers = {}
    
    def parse_file(self, file_path: str, content: str) -> Tuple[List[ParsedNode], List[ParsedRelationship]]:
        """Parse a source file and extract nodes and relationships."""
        
        # Determine file type
        file_ext = Path(file_path).suffix.lower()
        language = self._detect_language(file_ext)
        
        if language in self.parsers:
            return self._parse_with_treesitter(content, language)
        else:
            return self._parse_with_regex(content, language)
    
    def _detect_language(self, file_ext: str) -> str:
        """Detect programming language from file extension."""
        ext_map = {
            '.ts': 'typescript',
            '.tsx': 'tsx',
            '.js': 'javascript',
            '.jsx': 'jsx',
            '.py': 'python',
            '.java': 'java',
            '.cpp': 'cpp',
            '.hpp': 'cpp',
            '.c': 'c',
            '.h': 'c'
        }
        return ext_map.get(file_ext, 'unknown')
    
    def _parse_with_treesitter(self, content: str, language: str) -> Tuple[List[ParsedNode], List[ParsedRelationship]]:
        """Parse using TreeSitter (when available)."""
        # This would contain the actual TreeSitter parsing logic
        # For now, fall back to regex parsing
        logger.debug(f"TreeSitter parsing for {language} - falling back to regex")
        return self._parse_with_regex(content, language)
    
    def _parse_with_regex(self, content: str, language: str) -> Tuple[List[ParsedNode], List[ParsedRelationship]]:
        """Parse using regex patterns as fallback."""
        nodes = []
        relationships = []
        
        lines = content.split('\n')
        
        if language in ['typescript', 'tsx', 'javascript', 'jsx']:
            nodes, relationships = self._parse_typescript_regex(lines)
        elif language == 'python':
            nodes, relationships = self._parse_python_regex(lines)
        
        return nodes, relationships
    
    def _parse_typescript_regex(self, lines: List[str]) -> Tuple[List[ParsedNode], List[ParsedRelationship]]:
        """Parse TypeScript/JavaScript using regex patterns."""
        nodes = []
        relationships = []
        
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            
            # Function declarations
            func_match = re.match(r'^\s*(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\((.*?)\)', stripped)
            if func_match:
                name = func_match.group(1)
                params = func_match.group(2)
                nodes.append(ParsedNode(
                    node_type='function',
                    name=name,
                    signature=f"function {name}({params})",
                    start_line=i,
                    metadata={'parameters': params.split(',') if params else []}
                ))
            
            # Arrow functions
            arrow_match = re.match(r'^\s*(?:export\s+)?const\s+(\w+)\s*=\s*\(([^)]*)\)\s*=>', stripped)
            if arrow_match:
                name = arrow_match.group(1)
                params = arrow_match.group(2)
                nodes.append(ParsedNode(
                    node_type='function',
                    name=name,
                    signature=f"const {name} = ({params}) =>",
                    start_line=i,
                    metadata={'parameters': params.split(',') if params else [], 'arrow_function': True}
                ))
            
            # Class declarations
            class_match = re.match(r'^\s*(?:export\s+)?class\s+(\w+)(?:\s+extends\s+(\w+))?', stripped)
            if class_match:
                name = class_match.group(1)
                parent = class_match.group(2)
                nodes.append(ParsedNode(
                    node_type='class',
                    name=name,
                    signature=f"class {name}" + (f" extends {parent}" if parent else ""),
                    start_line=i,
                    metadata={'parent_class': parent}
                ))
                
                # Add inheritance relationship
                if parent:
                    relationships.append(ParsedRelationship(
                        source_name=name,
                        target_name=parent,
                        relationship_type='inherits'
                    ))
            
            # Import statements
            import_match = re.match(r'^\s*import\s+(.+?)\s+from\s+[\'"](.+?)[\'"]', stripped)
            if import_match:
                imports = import_match.group(1)
                module = import_match.group(2)
                
                # Handle different import patterns
                if imports.startswith('{') and imports.endswith('}'):
                    # Named imports: import { a, b } from 'module'
                    named_imports = re.findall(r'\w+', imports[1:-1])
                    for imp in named_imports:
                        nodes.append(ParsedNode(
                            node_type='import',
                            name=imp,
                            signature=f"import {{ {imp} }} from '{module}'",
                            start_line=i,
                            metadata={'module': module, 'import_type': 'named'}
                        ))
                        relationships.append(ParsedRelationship(
                            source_name=imp,
                            target_name=module,
                            relationship_type='imports'
                        ))
                else:
                    # Default import: import name from 'module'
                    import_name = imports.strip()
                    nodes.append(ParsedNode(
                        node_type='import',
                        name=import_name,
                        signature=f"import {import_name} from '{module}'",
                        start_line=i,
                        metadata={'module': module, 'import_type': 'default'}
                    ))
                    relationships.append(ParsedRelationship(
                        source_name=import_name,
                        target_name=module,
                        relationship_type='imports'
                    ))
            
            # Function calls (basic detection)
            call_matches = re.findall(r'(\w+)\s*\(', stripped)
            for call in call_matches:
                # This is a very basic approach - would need more sophisticated parsing
                # to determine the actual calling context
                if call not in ['if', 'for', 'while', 'switch', 'function', 'class']:
                    relationships.append(ParsedRelationship(
                        source_name='unknown',  # Would need context to determine caller
                        target_name=call,
                        relationship_type='calls',
                        metadata={'line': i}
                    ))
        
        return nodes, relationships
    
    def _parse_python_regex(self, lines: List[str]) -> Tuple[List[ParsedNode], List[ParsedRelationship]]:
        """Parse Python using regex patterns."""
        nodes = []
        relationships = []
        
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            
            # Function definitions
            func_match = re.match(r'^\s*def\s+(\w+)\s*\((.*?)\):', stripped)
            if func_match:
                name = func_match.group(1)
                params = func_match.group(2)
                nodes.append(ParsedNode(
                    node_type='function',
                    name=name,
                    signature=f"def {name}({params}):",
                    start_line=i,
                    metadata={'parameters': [p.strip() for p in params.split(',') if p.strip()]}
                ))
            
            # Class definitions
            class_match = re.match(r'^\s*class\s+(\w+)(?:\(([^)]+)\))?:', stripped)
            if class_match:
                name = class_match.group(1)
                parents = class_match.group(2)
                nodes.append(ParsedNode(
                    node_type='class',
                    name=name,
                    signature=f"class {name}" + (f"({parents})" if parents else "") + ":",
                    start_line=i,
                    metadata={'parent_classes': [p.strip() for p in parents.split(',') if p.strip()] if parents else []}
                ))
                
                # Add inheritance relationships
                if parents:
                    for parent in parents.split(','):
                        parent = parent.strip()
                        if parent:
                            relationships.append(ParsedRelationship(
                                source_name=name,
                                target_name=parent,
                                relationship_type='inherits'
                            ))
            
            # Import statements
            import_match = re.match(r'^\s*(?:from\s+(\S+)\s+)?import\s+(.+)', stripped)
            if import_match:
                module = import_match.group(1)
                imports = import_match.group(2)
                
                import_items = [imp.strip() for imp in imports.split(',')]
                for imp in import_items:
                    nodes.append(ParsedNode(
                        node_type='import',
                        name=imp,
                        signature=f"{'from ' + module + ' ' if module else ''}import {imp}",
                        start_line=i,
                        metadata={'module': module, 'import_type': 'from' if module else 'direct'}
                    ))
                    relationships.append(ParsedRelationship(
                        source_name=imp,
                        target_name=module or imp,
                        relationship_type='imports'
                    ))
        
        return nodes, relationships


def should_ignore_file(file_path: str) -> bool:
    """Check if a file should be ignored during parsing."""
    ignore_patterns = [
        # Common directories to ignore
        'node_modules/', '.git/', '__pycache__/', '.pytest_cache/',
        'dist/', 'build/', '.vscode/', '.idea/',
        # Common file patterns to ignore
        '.min.js', '.bundle.js', '.test.', '.spec.',
        # Specific patterns from the original notebooks
        'types.ts', 'src/types/', 'src/styles/', 'src/stories/',
        'src/setup/', 'src/languages/', 'src/utils/', 'src/libs/API/parameters/'
    ]
    
    for pattern in ignore_patterns:
        if pattern in file_path:
            return True
    
    return False


def get_supported_extensions() -> List[str]:
    """Get list of supported file extensions."""
    return ['.ts', '.tsx', '.js', '.jsx', '.py', '.java', '.cpp', '.hpp', '.c', '.h']