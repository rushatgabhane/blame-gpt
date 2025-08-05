import logging
from pathlib import Path

import tree_sitter_python as tspython
from tree_sitter import Language, Parser, Query

logger = logging.getLogger(__name__)


class TreeSitterParser:
    """Tree-sitter based Python code parser"""

    def __init__(self):
        self.python_language = Language(tspython.language())
        self.parser = Parser(self.python_language)
        self._queries = {}
        self._load_queries()

    def _load_queries(self):
        """Load tree-sitter queries from .scm files"""
        queries_dir = Path(__file__).parent / "queries"

        # Load Python queries
        python_query_file = queries_dir / "python.scm"
        if python_query_file.exists():
            with open(python_query_file) as f:
                query_source = f.read()
            self._queries["python"] = Query(self.python_language, query_source)
            logger.debug("Loaded Python queries")
        else:
            logger.warning(f"Python query file not found: {python_query_file}")

    def parse_file(self, file_path: Path) -> tuple | None:
        """Parse a Python file and return tree + content"""
        try:
            with open(file_path, encoding="utf-8", errors="ignore") as f:
                content = f.read()

            tree = self.parser.parse(bytes(content, "utf8"))
            return tree, content

        except Exception as e:
            logger.error(f"Error parsing file {file_path}: {e}")
            return None

    def get_query(self, language: str = "python") -> Query | None:
        """Get tree-sitter query for specified language"""
        return self._queries.get(language)

    def query_captures(self, tree, content: str, language: str = "python"):
        """Execute queries and return captures"""
        query = self.get_query(language)
        if not query:
            return []

        try:
            captures = query.captures(tree.root_node)
            return list(captures)
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            return []
