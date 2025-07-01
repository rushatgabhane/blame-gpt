import json
import sqlite3
from . import codegraph_queries
import os
from typing import Optional, List, Dict, Any, Tuple
from libs import constants
from functools import wraps
import hashlib
from dataclasses import dataclass
from datetime import datetime

# Create a dedicated path for the code graph database
CODEGRAPH_DB_PATH = constants.CACHE_DB_PATH.replace('.db', '_codegraph.db')
os.makedirs(os.path.dirname(CODEGRAPH_DB_PATH), exist_ok=True)


@dataclass
class CodeNode:
    id: Optional[int]
    file_path: str
    node_type: str
    name: str
    full_name: Optional[str] = None
    signature: Optional[str] = None
    start_line: Optional[int] = None
    end_line: Optional[int] = None
    content_hash: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class CodeRelationship:
    id: Optional[int]
    source_node_id: int
    target_node_id: int
    relationship_type: str
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None


@dataclass
class CodeFile:
    id: Optional[int]
    file_path: str
    content_hash: str
    language: Optional[str] = None
    size_bytes: Optional[int] = None
    line_count: Optional[int] = None
    last_parsed: Optional[datetime] = None
    parse_status: str = 'pending'
    parse_error: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


def require_connection(method):
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        if self.connection is None:
            raise ValueError("database connection is not initialized.")
        return method(self, *args, **kwargs)
    return wrapper


class CodeGraphDatabase:
    def __init__(self, db_path: str = CODEGRAPH_DB_PATH):
        self.connection = sqlite3.connect(db_path, check_same_thread=False, timeout=15.0)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA journal_mode=WAL;")
        self.connection.execute("PRAGMA synchronous=NORMAL;")
        self.connection.execute("PRAGMA strict=ON;")
        self.connection.execute("PRAGMA foreign_keys=ON;")
        self._init_db()

    def _init_db(self):
        if self.connection is None:
            raise ValueError("database connection is not initialized.")
        
        self.connection.executescript(codegraph_queries.CREATE_TABLES)
        self.connection.commit()

    def close(self):
        if self.connection:
            self.connection.close()
            self.connection = None

    @staticmethod
    def compute_content_hash(content: str) -> str:
        """Compute SHA256 hash of content."""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    # File operations
    @require_connection
    def add_code_file(self, file_path: str, content_hash: str, language: str = None, 
                     size_bytes: int = None, line_count: int = None) -> None:
        """Add or update a code file record."""
        assert self.connection is not None
        self.connection.execute(
            codegraph_queries.INSERT_CODE_FILE,
            (file_path, content_hash, language, size_bytes, line_count, 
             datetime.now(), 'pending', None)
        )
        self.connection.commit()

    @require_connection
    def get_code_file(self, file_path: str) -> Optional[CodeFile]:
        """Get a code file by path."""
        assert self.connection is not None
        row = self.connection.execute(codegraph_queries.GET_CODE_FILE, (file_path,)).fetchone()
        if not row:
            return None
        
        return CodeFile(
            id=row['id'],
            file_path=row['file_path'],
            content_hash=row['content_hash'],
            language=row['language'],
            size_bytes=row['size_bytes'],
            line_count=row['line_count'],
            last_parsed=row['last_parsed'],
            parse_status=row['parse_status'],
            parse_error=row['parse_error'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )

    @require_connection
    def update_file_parse_status(self, file_path: str, status: str, error: str = None) -> None:
        """Update the parse status of a file."""
        assert self.connection is not None
        self.connection.execute(
            codegraph_queries.UPDATE_FILE_PARSE_STATUS,
            (status, error, file_path)
        )
        self.connection.commit()

    @require_connection
    def get_files_by_status(self, status: str) -> List[CodeFile]:
        """Get all files with a specific parse status."""
        assert self.connection is not None
        rows = self.connection.execute(codegraph_queries.GET_FILES_BY_STATUS, (status,)).fetchall()
        
        return [
            CodeFile(
                id=row['id'],
                file_path=row['file_path'],
                content_hash=row['content_hash'],
                language=row['language'],
                size_bytes=row['size_bytes'],
                line_count=row['line_count'],
                last_parsed=row['last_parsed'],
                parse_status=row['parse_status'],
                parse_error=row['parse_error'],
                created_at=row['created_at'],
                updated_at=row['updated_at']
            )
            for row in rows
        ]

    # Node operations
    @require_connection
    def add_code_node(self, node: CodeNode) -> int:
        """Add a code node and return its ID."""
        assert self.connection is not None
        
        metadata_json = json.dumps(node.metadata) if node.metadata else None
        
        cursor = self.connection.execute(
            codegraph_queries.INSERT_CODE_NODE,
            (node.file_path, node.node_type, node.name, node.full_name,
             node.signature, node.start_line, node.end_line, 
             node.content_hash, metadata_json)
        )
        self.connection.commit()
        return cursor.lastrowid

    @require_connection
    def get_nodes_by_file(self, file_path: str) -> List[CodeNode]:
        """Get all nodes in a specific file."""
        assert self.connection is not None
        rows = self.connection.execute(codegraph_queries.GET_NODES_BY_FILE, (file_path,)).fetchall()
        
        return [self._row_to_code_node(row) for row in rows]

    @require_connection
    def get_nodes_by_type(self, node_type: str) -> List[CodeNode]:
        """Get all nodes of a specific type."""
        assert self.connection is not None
        rows = self.connection.execute(codegraph_queries.GET_NODES_BY_TYPE, (node_type,)).fetchall()
        
        return [self._row_to_code_node(row) for row in rows]

    @require_connection
    def get_node_by_id(self, node_id: int) -> Optional[CodeNode]:
        """Get a node by its ID."""
        assert self.connection is not None
        row = self.connection.execute(codegraph_queries.GET_NODE_BY_ID, (node_id,)).fetchone()
        
        if not row:
            return None
        
        return self._row_to_code_node(row)

    @require_connection
    def search_nodes(self, query: str) -> List[CodeNode]:
        """Search for nodes by name."""
        assert self.connection is not None
        pattern = f"%{query}%"
        rows = self.connection.execute(codegraph_queries.SEARCH_NODES, (pattern, pattern)).fetchall()
        
        return [self._row_to_code_node(row) for row in rows]

    @require_connection
    def delete_nodes_by_file(self, file_path: str) -> None:
        """Delete all nodes for a specific file."""
        assert self.connection is not None
        # First delete relationships
        self.connection.execute(codegraph_queries.DELETE_RELATIONSHIPS_BY_FILE, (file_path, file_path))
        # Then delete nodes
        self.connection.execute(codegraph_queries.DELETE_NODES_BY_FILE, (file_path,))
        self.connection.commit()

    def _row_to_code_node(self, row) -> CodeNode:
        """Convert a database row to a CodeNode object."""
        metadata = json.loads(row['metadata']) if row['metadata'] else None
        
        return CodeNode(
            id=row['id'],
            file_path=row['file_path'],
            node_type=row['node_type'],
            name=row['name'],
            full_name=row['full_name'],
            signature=row['signature'],
            start_line=row['start_line'],
            end_line=row['end_line'],
            content_hash=row['content_hash'],
            metadata=metadata,
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )

    # Relationship operations
    @require_connection
    def add_code_relationship(self, relationship: CodeRelationship) -> int:
        """Add a code relationship and return its ID."""
        assert self.connection is not None
        
        metadata_json = json.dumps(relationship.metadata) if relationship.metadata else None
        
        cursor = self.connection.execute(
            codegraph_queries.INSERT_CODE_RELATIONSHIP,
            (relationship.source_node_id, relationship.target_node_id,
             relationship.relationship_type, metadata_json)
        )
        self.connection.commit()
        return cursor.lastrowid

    @require_connection
    def get_relationships_from_node(self, node_id: int) -> List[Dict[str, Any]]:
        """Get all relationships where the node is the source."""
        assert self.connection is not None
        rows = self.connection.execute(codegraph_queries.GET_RELATIONSHIPS_FROM_NODE, (node_id,)).fetchall()
        
        return [dict(row) for row in rows]

    @require_connection
    def get_relationships_to_node(self, node_id: int) -> List[Dict[str, Any]]:
        """Get all relationships where the node is the target."""
        assert self.connection is not None
        rows = self.connection.execute(codegraph_queries.GET_RELATIONSHIPS_TO_NODE, (node_id,)).fetchall()
        
        return [dict(row) for row in rows]

    @require_connection
    def get_relationships_by_type(self, relationship_type: str) -> List[Dict[str, Any]]:
        """Get all relationships of a specific type."""
        assert self.connection is not None
        rows = self.connection.execute(codegraph_queries.GET_RELATIONSHIPS_BY_TYPE, (relationship_type,)).fetchall()
        
        return [dict(row) for row in rows]

    # Graph analysis queries
    @require_connection
    def get_function_call_graph(self) -> List[Dict[str, Any]]:
        """Get the function call graph."""
        assert self.connection is not None
        rows = self.connection.execute(codegraph_queries.GET_FUNCTION_CALL_GRAPH).fetchall()
        
        return [dict(row) for row in rows]

    @require_connection
    def get_import_dependencies(self) -> List[Dict[str, Any]]:
        """Get import dependencies."""
        assert self.connection is not None
        rows = self.connection.execute(codegraph_queries.GET_IMPORT_DEPENDENCIES).fetchall()
        
        return [dict(row) for row in rows]

    @require_connection
    def get_class_hierarchy(self) -> List[Dict[str, Any]]:
        """Get class inheritance hierarchy."""
        assert self.connection is not None
        rows = self.connection.execute(codegraph_queries.GET_CLASS_HIERARCHY).fetchall()
        
        return [dict(row) for row in rows]

    # Statistics
    @require_connection
    def get_node_stats(self) -> List[Dict[str, Any]]:
        """Get statistics about nodes by type."""
        assert self.connection is not None
        rows = self.connection.execute(codegraph_queries.COUNT_NODES_BY_TYPE).fetchall()
        
        return [dict(row) for row in rows]

    @require_connection
    def get_relationship_stats(self) -> List[Dict[str, Any]]:
        """Get statistics about relationships by type."""
        assert self.connection is not None
        rows = self.connection.execute(codegraph_queries.COUNT_RELATIONSHIPS_BY_TYPE).fetchall()
        
        return [dict(row) for row in rows]

    @require_connection
    def get_files_summary(self) -> Dict[str, Any]:
        """Get summary of file parsing status."""
        assert self.connection is not None
        row = self.connection.execute(codegraph_queries.GET_FILES_SUMMARY).fetchone()
        
        return dict(row) if row else {}