"""
Entity extraction module for code analysis using tree-sitter parsers.
Extracts functions, classes, variables, imports, exports, and function calls from JavaScript/TypeScript files.
"""

from pathlib import Path
from typing import Any, Dict, List  # noqa: UP035

import tree_sitter_javascript
import tree_sitter_typescript
from tree_sitter import Language, Parser


class EntityExtractor:
    def __init__(self):
        """Initialize tree-sitter parsers for JavaScript and TypeScript."""
        # JavaScript parser
        self.js_language = Language(tree_sitter_javascript.language())
        self.js_parser = Parser(self.js_language)
        
        # TypeScript parser
        try:
            self.ts_language = Language(tree_sitter_typescript.language_typescript())
            self.ts_parser = Parser(self.ts_language)
        except AttributeError:
            print("⚠️ TypeScript parser not available")
            self.ts_parser = None
            self.ts_language = None

    def analyze_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Analyze a single file and extract all entities.
        
        Args:
            file_path: Path to the JavaScript/TypeScript file
            
        Returns:
            Dictionary containing extracted entities and metadata
        """
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
            buf = content.encode("utf-8")
            
            # Choose appropriate parser
            parser = self.ts_parser if file_path.suffix in (".ts", ".tsx") else self.js_parser
            if parser is None:
                parser = self.js_parser
                
            tree = parser.parse(buf)
            root = tree.root_node

            # Extract all entity types
            functions = self._extract_functions(root, buf)
            classes = self._extract_classes(root, buf)
            imports = self._extract_imports(root, buf)
            exports = self._extract_exports(root, buf)
            function_calls = self._extract_function_calls(root, buf)
            variables = self._extract_variables(root, buf)

            return {
                "file_path": str(file_path.resolve()),
                "success": True,
                "functions": functions,
                "classes": classes,
                "imports": imports,
                "exports": exports,
                "function_calls": function_calls,
                "variables": variables,
                "total_entities": len(functions) + len(classes) + len(variables)
            }
        except Exception as e:
            return {
                "file_path": str(file_path),
                "success": False,
                "error": str(e),
                "functions": [],
                "classes": [],
                "imports": [],
                "exports": [],
                "function_calls": [],
                "variables": [],
                "total_entities": 0
            }

    def _node_text(self, node, buf: bytes) -> str:
        """Extract text from a node."""
        try:
            return buf[node.start_byte:node.end_byte].decode("utf-8", errors="replace")
        except Exception:
            return ""

    def _lines(self, node) -> tuple[int, int]:
        """Get start and end line numbers for a node."""
        return node.start_point[0] + 1, node.end_point[0] + 1

    def _extract_functions(self, root, buf: bytes) -> List[Dict[str, Any]]:
        """Extract all function declarations from the AST."""
        functions = []
        
        def walk(node):
            if node.type == "function_declaration":
                ident = next((c for c in node.children if c.type == "identifier"), None)
                if ident:
                    start_line, end_line = self._lines(node)
                    functions.append({
                        "name": self._node_text(ident, buf),
                        "type": "function",
                        "start_line": start_line,
                        "end_line": end_line,
                        "ast_type": "function_declaration"
                    })
            elif node.type == "variable_declaration":
                for decl in node.children:
                    if decl.type != "variable_declarator":
                        continue
                    ident = next((c for c in decl.children if c.type == "identifier"), None)
                    arrow = next((c for c in decl.children if c.type == "arrow_function"), None)
                    if ident and arrow:
                        start_line, end_line = self._lines(arrow)
                        functions.append({
                            "name": self._node_text(ident, buf),
                            "type": "function",
                            "start_line": start_line,
                            "end_line": end_line,
                            "ast_type": "arrow_function"
                        })
            elif node.type == "method_definition":
                ident = next((c for c in node.children if c.type == "property_identifier"), None)
                if ident:
                    start_line, end_line = self._lines(node)
                    functions.append({
                        "name": self._node_text(ident, buf),
                        "type": "method",
                        "start_line": start_line,
                        "end_line": end_line,
                        "ast_type": "method_definition"
                    })
            elif node.type == "assignment_expression":
                left = next((c for c in node.children if c.type == "identifier"), None)
                fnexp = next((c for c in node.children if c.type == "function_expression"), None)
                if left and fnexp:
                    start_line, end_line = self._lines(fnexp)
                    functions.append({
                        "name": self._node_text(left, buf),
                        "type": "function",
                        "start_line": start_line,
                        "end_line": end_line,
                        "ast_type": "function_expression"
                    })
            
            for child in node.children:
                walk(child)
                
        walk(root)
        return functions

    def _extract_classes(self, root, buf: bytes) -> List[Dict[str, Any]]:
        """Extract all class declarations from the AST."""
        classes = []
        
        def walk(node):
            if node.type == "class_declaration":
                ident = next((c for c in node.children if c.type == "identifier"), None)
                if ident:
                    start_line, end_line = self._lines(node)
                    classes.append({
                        "name": self._node_text(ident, buf),
                        "type": "class",
                        "start_line": start_line,
                        "end_line": end_line,
                        "ast_type": "class_declaration"
                    })
            
            for child in node.children:
                walk(child)
                
        walk(root)
        return classes

    def _extract_imports(self, root, buf: bytes) -> List[Dict[str, Any]]:
        """Extract all import statements from the AST."""
        imports = []
        
        def walk(node):
            if node.type in ("import_statement", "import_declaration"):
                src_line, _ = self._lines(node)
                module = ""
                alias_map = {}
                
                for child in node.children:
                    if child.type == "string":
                        module = self._node_text(child, buf).strip("'\"")
                    elif child.type == "import_clause":
                        # Default import
                        default_ident = next((sc for sc in child.children if sc.type == "identifier"), None)
                        if default_ident:
                            alias_map[self._node_text(default_ident, buf)] = "default"
                        
                        # Named imports
                        named_group = next((sc for sc in child.children if sc.type == "named_imports"), None)
                        if named_group:
                            for spec in named_group.children:
                                if spec.type != "import_specifier":
                                    continue
                                idents = [sc for sc in spec.children if sc.type == "identifier"]
                                if len(idents) == 1:  # import { foo }
                                    alias_map[self._node_text(idents[0], buf)] = self._node_text(idents[0], buf)
                                elif len(idents) == 2:  # import { foo as bar }
                                    alias_map[self._node_text(idents[1], buf)] = self._node_text(idents[0], buf)
                
                imports.append({
                    "type": "import",
                    "module": module,
                    "alias_map": alias_map,
                    "line": src_line
                })
            
            for child in node.children:
                walk(child)
                
        walk(root)
        return imports

    def _extract_exports(self, root, buf: bytes) -> List[Dict[str, Any]]:
        """Extract all export statements from the AST."""
        exports = []
        
        def walk(node):
            if node.type in ("export_statement", "export_declaration"):
                sline, _ = self._lines(node)
                exported = []
                etype = "named"
                
                text_low = self._node_text(node, buf).lower()
                if "default" in text_low and node.type == "export_statement":
                    exported.append("__DEFAULT__")
                    etype = "default"
                
                # Explicit names
                for child in node.children:
                    if child.type in ("function_declaration", "class_declaration"):
                        ident = next((sc for sc in child.children if sc.type == "identifier"), None)
                        if ident:
                            exported.append(self._node_text(ident, buf))
                    elif child.type == "variable_declaration":
                        ident = next((sc for sc in child.children if sc.type == "variable_declarator"), None)
                        if ident:
                            id2 = next((x for x in ident.children if x.type == "identifier"), None)
                            if id2:
                                exported.append(self._node_text(id2, buf))
                    elif child.type == "export_clause":  # { foo as bar }
                        for spec in child.children:
                            if spec.type != "export_specifier":
                                continue
                            ids = [x for x in spec.children if x.type == "identifier"]
                            if ids:
                                exported.append(self._node_text(ids[-1], buf))  # alias (or original)
                
                exports.append({
                    "type": "export",
                    "export_type": etype,
                    "exported_names": exported,
                    "line": sline
                })
            
            for child in node.children:
                walk(child)
                
        walk(root)
        return exports

    def _extract_function_calls(self, root, buf: bytes) -> List[Dict[str, Any]]:
        """Extract all function call expressions from the AST."""
        calls = []
        
        def walk(node):
            if node.type == "call_expression" and node.children:
                callee = node.children[0]
                line = callee.start_point[0] + 1
                
                if callee.type == "identifier":
                    calls.append({
                        "type": "function_call",
                        "target": self._node_text(callee, buf),
                        "line": line,
                        "call_type": "direct"
                    })
                elif callee.type == "member_expression":
                    calls.append({
                        "type": "function_call",
                        "target": self._node_text(callee, buf),
                        "line": line,
                        "call_type": "method"
                    })
                elif callee.type == "new_expression":
                    calls.append({
                        "type": "function_call",
                        "target": self._node_text(callee, buf),
                        "line": line,
                        "call_type": "constructor"
                    })
            
            for child in node.children:
                walk(child)
                
        walk(root)
        return calls

    def _extract_variables(self, root, buf: bytes) -> List[Dict[str, Any]]:
        """Extract all variable declarations from the AST."""
        variables = []
        
        def walk(node):
            if node.type == "variable_declaration":
                var_kw = self._node_text(node, buf)[:6]
                vtype = "constant" if "const" in var_kw else "variable"
                
                for decl in node.children:
                    if decl.type != "variable_declarator":
                        continue
                    ident = next((c for c in decl.children if c.type == "identifier"), None)
                    if ident:
                        start_line, end_line = self._lines(decl)
                        variables.append({
                            "name": self._node_text(ident, buf),
                            "type": vtype,
                            "start_line": start_line,
                            "end_line": end_line,
                            "ast_type": "variable_declaration"
                        })
            
            for child in node.children:
                walk(child)
                
        walk(root)
        return variables