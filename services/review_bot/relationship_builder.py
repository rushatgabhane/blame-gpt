"""
Relationship builder module for creating connections between code entities.
Builds file relationships, function calls, cross-file dependencies, and entity relationships.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional


class RelationshipBuilder:
    def __init__(self, repo_dir: Path):
        """
        Initialize relationship builder.
        
        Args:
            repo_dir: Root directory of the repository
        """
        self.repo_dir = repo_dir

    def build_all_relationships(self, analyses: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Build all types of relationships from entity analysis results.
        
        Args:
            analyses: List of entity analysis results from EntityExtractor
            
        Returns:
            Dictionary containing all relationship types
        """
        file_relationships = self.build_file_relationships(analyses)
        export_relationships = self.build_export_relationships(analyses)
        function_call_relationships = self.build_function_call_relationships(analyses)
        cross_file_call_relationships = self.build_cross_file_function_calls(analyses, file_relationships)
        entity_relationships = self.build_entity_relationships(analyses)
        variable_relationships = self.build_variable_usage_relationships(analyses)

        return {
            'file_relationships': file_relationships,
            'export_relationships': export_relationships,
            'function_call_relationships': function_call_relationships,
            'cross_file_call_relationships': cross_file_call_relationships,
            'entity_relationships': entity_relationships,
            'variable_relationships': variable_relationships
        }

    def resolve_import_path(self, import_path: str, cur_file: str) -> Optional[str]:
        """
        Resolve an import path to an actual file path.
        
        Args:
            import_path: The import path string
            cur_file: Current file path
            
        Returns:
            Resolved file path or None if not found
        """
        try:
            cur_dir = Path(cur_file).parent
            candidate = None

            if import_path.startswith(("./", "../")):
                # Relative import
                candidate = (cur_dir / import_path).resolve()
            else:
                # Treat bare specifier as project-local if it doesn't look external
                if not import_path.startswith(("@", "react", "lodash", "underscore")):
                    candidate = (self.repo_dir / "src" / import_path).resolve()
            
            if candidate:
                for ext in (".js", ".jsx", ".ts", ".tsx", "/index.js", "/index.ts", "/index.tsx"):
                    p = Path(str(candidate) + ext)
                    if p.exists():
                        return str(p)
            return None
        except Exception:
            return None

    def build_file_relationships(self, analyses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Build import/export relationships between files.
        
        Args:
            analyses: List of entity analysis results
            
        Returns:
            List of file relationship dictionaries
        """
        relationships = []
        
        for analysis in analyses:
            if not analysis["success"]:
                continue
                
            source_file = analysis["file_path"]
            
            for imp in analysis["imports"]:
                target_file = self.resolve_import_path(imp["module"], source_file)
                
                if target_file:
                    # Internal import
                    relationships.append({
                        "type": "imports",
                        "source_file": source_file,
                        "target_file": target_file,
                        "import_line": imp["line"],
                        "import_stmt": imp["module"],
                        "alias_map": imp["alias_map"]
                    })
                else:
                    # External import
                    relationships.append({
                        "type": "external_import",
                        "source_file": source_file,
                        "target_module": imp["module"],
                        "import_line": imp["line"],
                        "import_stmt": imp["module"],
                        "alias_map": imp["alias_map"]
                    })
        
        return relationships

    def build_export_relationships(self, analyses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Build export relationships for files.
        
        Args:
            analyses: List of entity analysis results
            
        Returns:
            List of export relationship dictionaries
        """
        relationships = []
        
        for analysis in analyses:
            if not analysis["success"]:
                continue
                
            for export in analysis["exports"]:
                for name in export["exported_names"]:
                    relationships.append({
                        "type": "exports",
                        "source_file": analysis["file_path"],
                        "exported_name": name,
                        "export_type": export["export_type"],
                        "export_line": export["line"]
                    })
        
        return relationships

    def build_function_call_relationships(self, analyses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Build function call relationships within files.
        
        Args:
            analyses: List of entity analysis results
            
        Returns:
            List of function call relationship dictionaries
        """
        relationships = []
        
        for analysis in analyses:
            if not analysis["success"]:
                continue
                
            source_file = analysis["file_path"]
            
            for call in analysis["function_calls"]:
                if "." in call["target"]:
                    # Method call
                    obj, method = call["target"].split(".", 1)
                    relationships.append({
                        "type": "function_call",
                        "call_type": "method_call",
                        "source_file": source_file,
                        "target_object": obj,
                        "target_method": method,
                        "line": call["line"]
                    })
                else:
                    # Direct function call
                    relationships.append({
                        "type": "function_call",
                        "call_type": "direct_call",
                        "source_file": source_file,
                        "target_function": call["target"],
                        "line": call["line"]
                    })
        
        return relationships

    def build_cross_file_function_calls(
        self, 
        analyses: List[Dict[str, Any]], 
        file_rels: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Build cross-file function call relationships using import information.
        
        Args:
            analyses: List of entity analysis results
            file_rels: File relationship results
            
        Returns:
            List of cross-file call relationship dictionaries
        """
        # Build alias map: {file -> {alias -> target_file}}
        alias_map = {}
        for rel in file_rels:
            if rel["type"] != "imports":
                continue
            source_file = rel["source_file"]
            target_file = rel["target_file"]
            
            for alias_name, _orig in rel["alias_map"].items():
                alias_map.setdefault(source_file, {})[alias_name] = target_file

        relationships = []
        
        for analysis in analyses:
            if not analysis["success"]:
                continue
                
            source_file = analysis["file_path"]
            file_aliases = alias_map.get(source_file, {})
            
            for call in analysis["function_calls"]:
                target_name = call["target"].split(".", 1)[0]  # Get object or function name
                
                if target_name in file_aliases:
                    relationships.append({
                        "type": "cross_file_call",
                        "source_file": source_file,
                        "target_file": file_aliases[target_name],
                        "function_name": target_name,
                        "line": call["line"]
                    })
        
        return relationships

    def build_entity_relationships(self, analyses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Build relationships between entities (classes, methods, functions).
        
        Args:
            analyses: List of entity analysis results
            
        Returns:
            List of entity relationship dictionaries
        """
        relationships = []
        
        for analysis in analyses:
            if not analysis["success"]:
                continue
                
            source_file = analysis["file_path"]
            
            # Class to method relationships
            class_names = [c["name"] for c in analysis["classes"]]
            for func in analysis["functions"]:
                if func["ast_type"] == "method_definition":
                    for class_name in class_names:
                        relationships.append({
                            "type": "class_has_method",
                            "source_entity": class_name,
                            "target_entity": func["name"],
                            "source_file": source_file,
                            "target_file": source_file
                        })
            
            # Function to function call relationships (within file)
            for func in analysis["functions"]:
                start_line, end_line = func["start_line"], func["end_line"]
                
                for call in analysis["function_calls"]:
                    if start_line <= call["line"] <= end_line:
                        relationships.append({
                            "type": "function_calls",
                            "source_entity": func["name"],
                            "target_call": call["target"],
                            "source_file": source_file,
                            "call_line": call["line"]
                        })
        
        return relationships

    def build_variable_usage_relationships(self, analyses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Build variable usage relationships.
        
        Args:
            analyses: List of entity analysis results
            
        Returns:
            List of variable usage relationship dictionaries
        """
        relationships = []
        
        for analysis in analyses:
            if not analysis["success"]:
                continue
                
            source_file = analysis["file_path"]
            
            # Create variable name to declaration line mapping
            var_declarations = {v["name"]: v["start_line"] for v in analysis["variables"]}
            
            for call in analysis["function_calls"]:
                call_head = call["target"].split(".", 1)[0]
                
                if call_head in var_declarations:
                    relationships.append({
                        "type": "variable_usage",
                        "source_file": source_file,
                        "variable_name": call_head,
                        "usage_line": call["line"],
                        "declaration_line": var_declarations[call_head],
                        "usage_context": call["target"]
                    })
        
        return relationships