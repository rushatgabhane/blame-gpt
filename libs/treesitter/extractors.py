"""Simple entity extractor using tree-sitter"""

import hashlib
import logging
from pathlib import Path

from models.models import CodeEntity, FileAnalysis, FunctionCall

from .parser import TreeSitterParser

logger = logging.getLogger(__name__)


class PythonEntityExtractor:
    def __init__(self):
        self.parser = TreeSitterParser()

    def extract_from_file(self, file_path: Path) -> FileAnalysis | None:
        try:
            result = self.parser.parse_file(file_path)
            if not result:
                return None

            tree, content = result
            entities = []
            imports = []

            # Traversal of the AST
            self._extract_from_node(tree.root_node, content, str(file_path), entities, imports)

            file_hash = hashlib.md5(content.encode()).hexdigest()

            return FileAnalysis(
                file_path=str(file_path), language="python", entities=entities, imports=imports, file_hash=file_hash
            )

        except Exception as e:
            logger.error(f"Error extracting from {file_path}: {e}")
            return None

    def _extract_from_node(
        self,
        node,
        content: str,
        file_path: str,
        entities: list[CodeEntity],
        imports: list[str],
        parent_class: str = None,
    ):
        """Recursively extract entities from AST nodes"""

        if node.type == "function_definition":
            entity = self._make_function_entity(node, content, file_path, parent_class)
            if entity:
                entities.append(entity)

        elif node.type == "class_definition":
            entity = self._make_class_entity(node, content, file_path)
            if entity:
                entities.append(entity)
                # Process methods with class as parent
                for child in node.children:
                    self._extract_from_node(child, content, file_path, entities, imports, entity.name)

        elif node.type in ["import_statement", "import_from_statement"]:
            import_text = content[node.start_byte : node.end_byte]
            imports.append(import_text.strip())

        # Recurse into children (except for classes where we handle methods specially)
        if node.type != "class_definition":
            for child in node.children:
                self._extract_from_node(child, content, file_path, entities, imports, parent_class)

    def _make_function_entity(self, node, content: str, file_path: str, parent_class: str = None) -> CodeEntity | None:
        """Create function/method entity"""
        try:
            # Get function name
            name = self._get_node_text(node, content, "identifier")
            if not name:
                return None

            # Generate unique ID
            parent_prefix = f"{parent_class}." if parent_class else ""
            entity_id = f"{file_path}:{parent_prefix}{name}"

            # Get signature (name + parameters)
            signature = name
            params_node = self._find_child(node, "parameters")
            if params_node:
                params = content[params_node.start_byte : params_node.end_byte]
                signature = f"{name}{params}"

            # Get line numbers
            start_line = node.start_point.row + 1  # Convert from 0-indexed to 1-indexed
            end_line = node.end_point.row + 1

            # Get docstring
            docstring = self._get_docstring(node, content)

            # Find function calls within this function
            calls = self._find_function_calls(node, content)

            entity_type = "method" if parent_class else "function"

            return CodeEntity(
                id=entity_id,
                name=name,
                type=entity_type,
                file_path=file_path,
                signature=signature,
                docstring=docstring,
                parent=parent_class,
                calls=calls,
                start_line=start_line,
                end_line=end_line,
            )
        except Exception as e:
            logger.debug(f"Error creating function entity: {e}")
            return None

    def _make_class_entity(self, node, content: str, file_path: str) -> CodeEntity | None:
        """Create class entity"""
        try:
            name = self._get_node_text(node, content, "identifier")
            if not name:
                return None

            # Generate unique ID
            entity_id = f"{file_path}:{name}"

            # Get line numbers
            start_line = node.start_point.row + 1  # Convert from 0-indexed to 1-indexed
            end_line = node.end_point.row + 1

            docstring = self._get_docstring(node, content)

            return CodeEntity(
                id=entity_id,
                name=name,
                type="class",
                file_path=file_path,
                docstring=docstring,
                start_line=start_line,
                end_line=end_line,
            )
        except Exception as e:
            logger.debug(f"Error creating class entity: {e}")
            return None

    def _get_node_text(self, node, content: str, node_type: str) -> str | None:
        """Get text from first direct child of specified type"""
        # For function definitions, the identifier should be a direct child
        for child in node.children:
            if child.type == node_type:
                text = content[child.start_byte : child.end_byte]
                # Validate that it's a proper identifier (no whitespace, parentheses, etc.)
                if text and text.replace("_", "").replace(".", "").isalnum():
                    return text
        return None

    def _find_child(self, node, node_type: str):
        """Find first child of specified type"""
        for child in node.children:
            if child.type == node_type:
                return child
        return None

    def _get_docstring(self, node, content: str) -> str | None:
        """Extract docstring from function or class"""
        try:
            body = self._find_child(node, "block")
            if not body:
                return None

            # Look for first string in body
            for child in body.children:
                if child.type == "expression_statement":
                    string_node = self._find_child(child, "string")
                    if string_node:
                        text = content[string_node.start_byte : string_node.end_byte]
                        # Remove quotes
                        if text.startswith('"""') or text.startswith("'''"):
                            return text[3:-3].strip()
                        elif text.startswith('"') or text.startswith("'"):
                            return text[1:-1].strip()
            return None
        except Exception:
            return None

    def _find_function_calls(self, node, content: str) -> list[FunctionCall]:
        """Find all function and method calls within this node"""
        calls = []

        def traverse(n):
            if n.type == "call":
                call_info = self._extract_call_info(n, content)
                if call_info:
                    calls.append(call_info)

            # Recurse into children
            for child in n.children:
                traverse(child)

        traverse(node)
        # Remove duplicates based on full_call text
        seen = set()
        unique_calls = []
        for call in calls:
            if call.full_call not in seen:
                seen.add(call.full_call)
                unique_calls.append(call)
        return unique_calls

    def _extract_call_info(self, call_node, content: str) -> FunctionCall | None:
        """Extract function call information including full call text"""
        try:
            # Get the full call text with parameters
            full_call = content[call_node.start_byte : call_node.end_byte]

            # Clean up the call text: replace newlines with spaces and normalize whitespace
            full_call = " ".join(full_call.split())

            # Get just the function name/path for target
            target = None
            for child in call_node.children:
                if child.type in ["identifier", "attribute", "subscript"]:
                    target = content[child.start_byte : child.end_byte]
                    break

            if not target:
                return None

            return FunctionCall(
                target=target,
                full_call=full_call,
                is_internal=False,  # Will be updated later during resolution
            )
        except Exception:
            return None

    def _extract_call_name(self, call_node, content: str) -> str | None:
        """Extract the name of a function/method call, handles chained calls like a.b.c()"""
        try:
            # The first child should be the function being called
            for child in call_node.children:
                if child.type in ["identifier", "attribute", "subscript"]:
                    # Get the full text of the function expression
                    # This handles: func(), obj.method(), a.b.c(), arr[0](), etc.
                    call_name = content[child.start_byte : child.end_byte]
                    return call_name

            return None
        except Exception:
            return None
