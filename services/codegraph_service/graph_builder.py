"""
Code graph builder service.

This service orchestrates parsing source code files and building 
a queryable code graph stored in SQLite.
"""

import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from libs.sqlite.codegraph.codegraph_sqlite_client import (
    CodeGraphDatabase, CodeNode, CodeRelationship, CodeFile
)
from .treesitter_parser import TreeSitterParser, should_ignore_file, get_supported_extensions

logger = logging.getLogger(__name__)


class CodeGraphBuilder:
    """Builds and maintains a code graph from source files."""
    
    def __init__(self, db_path: str = None):
        self.db = CodeGraphDatabase(db_path) if db_path else CodeGraphDatabase()
        self.parser = TreeSitterParser()
    
    def index_directory(self, directory_path: str, recursive: bool = True) -> Dict[str, Any]:
        """Index all supported files in a directory."""
        directory_path = Path(directory_path).resolve()
        
        if not directory_path.exists():
            raise ValueError(f"Directory does not exist: {directory_path}")
        
        logger.info(f"Starting to index directory: {directory_path}")
        
        stats = {
            'total_files': 0,
            'processed_files': 0,
            'error_files': 0,
            'skipped_files': 0,
            'total_nodes': 0,
            'total_relationships': 0,
            'errors': []
        }
        
        # Get all source files
        source_files = self._find_source_files(directory_path, recursive)
        stats['total_files'] = len(source_files)
        
        logger.info(f"Found {len(source_files)} source files to process")
        
        for file_path in source_files:
            try:
                result = self.index_file(str(file_path))
                if result['success']:
                    stats['processed_files'] += 1
                    stats['total_nodes'] += result['nodes_added']
                    stats['total_relationships'] += result['relationships_added']
                else:
                    stats['error_files'] += 1
                    stats['errors'].append({
                        'file': str(file_path),
                        'error': result['error']
                    })
            except Exception as e:
                logger.error(f"Error processing file {file_path}: {e}")
                stats['error_files'] += 1
                stats['errors'].append({
                    'file': str(file_path),
                    'error': str(e)
                })
        
        logger.info(f"Indexing completed. Processed: {stats['processed_files']}, "
                   f"Errors: {stats['error_files']}, Nodes: {stats['total_nodes']}, "
                   f"Relationships: {stats['total_relationships']}")
        
        return stats
    
    def index_file(self, file_path: str) -> Dict[str, Any]:
        """Index a single source file."""
        file_path = Path(file_path).resolve()
        relative_path = self._get_relative_path(file_path)
        
        result = {
            'success': False,
            'file_path': str(file_path),
            'relative_path': relative_path,
            'nodes_added': 0,
            'relationships_added': 0,
            'error': None
        }
        
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Check if file needs to be re-parsed
            content_hash = self.db.compute_content_hash(content)
            existing_file = self.db.get_code_file(relative_path)
            
            if existing_file and existing_file.content_hash == content_hash and existing_file.parse_status == 'success':
                logger.debug(f"File {relative_path} is up to date, skipping")
                result['success'] = True
                return result
            
            # Add/update file record
            file_stats = self._get_file_stats(file_path, content)
            self.db.add_code_file(
                file_path=relative_path,
                content_hash=content_hash,
                language=file_stats['language'],
                size_bytes=file_stats['size_bytes'],
                line_count=file_stats['line_count']
            )
            
            # Remove existing nodes and relationships for this file
            self.db.delete_nodes_by_file(relative_path)
            
            # Parse the file
            nodes, relationships = self.parser.parse_file(str(file_path), content)
            
            # Add nodes to database
            node_id_map = {}  # Maps node names to their database IDs
            
            for node in nodes:
                code_node = CodeNode(
                    id=None,
                    file_path=relative_path,
                    node_type=node.node_type,
                    name=node.name,
                    full_name=node.full_name or f"{relative_path}::{node.name}",
                    signature=node.signature,
                    start_line=node.start_line,
                    end_line=node.end_line,
                    content_hash=self.db.compute_content_hash(node.content or ''),
                    metadata=node.metadata
                )
                
                node_id = self.db.add_code_node(code_node)
                node_id_map[node.name] = node_id
                result['nodes_added'] += 1
            
            # Add relationships to database
            for rel in relationships:
                source_id = node_id_map.get(rel.source_name)
                target_id = node_id_map.get(rel.target_name)
                
                # For now, only add relationships where both nodes exist in the same file
                # Cross-file relationships would need more sophisticated resolution
                if source_id and target_id:
                    code_rel = CodeRelationship(
                        id=None,
                        source_node_id=source_id,
                        target_node_id=target_id,
                        relationship_type=rel.relationship_type,
                        metadata=rel.metadata
                    )
                    
                    self.db.add_code_relationship(code_rel)
                    result['relationships_added'] += 1
            
            # Update file parse status
            self.db.update_file_parse_status(relative_path, 'success')
            result['success'] = True
            
            logger.debug(f"Successfully indexed {relative_path}: "
                        f"{result['nodes_added']} nodes, {result['relationships_added']} relationships")
        
        except Exception as e:
            logger.error(f"Error indexing file {file_path}: {e}")
            result['error'] = str(e)
            
            # Update file parse status to error
            try:
                self.db.update_file_parse_status(relative_path, 'error', str(e))
            except:
                pass  # Don't fail if we can't update the status
        
        return result
    
    def _find_source_files(self, directory: Path, recursive: bool = True) -> List[Path]:
        """Find all source files in a directory."""
        source_files = []
        supported_exts = get_supported_extensions()
        
        if recursive:
            for root, dirs, files in os.walk(directory):
                # Skip ignored directories
                dirs[:] = [d for d in dirs if not should_ignore_file(os.path.join(root, d) + '/')]
                
                for file in files:
                    file_path = Path(root) / file
                    relative_path = self._get_relative_path(file_path)
                    
                    if (file_path.suffix.lower() in supported_exts and 
                        not should_ignore_file(relative_path)):
                        source_files.append(file_path)
        else:
            for file_path in directory.iterdir():
                if file_path.is_file():
                    relative_path = self._get_relative_path(file_path)
                    
                    if (file_path.suffix.lower() in supported_exts and 
                        not should_ignore_file(relative_path)):
                        source_files.append(file_path)
        
        return source_files
    
    def _get_relative_path(self, file_path: Path) -> str:
        """Get relative path for storage in database."""
        # Try to get relative path from common project roots
        cwd = Path.cwd()
        try:
            return str(file_path.relative_to(cwd))
        except ValueError:
            # If file is not relative to cwd, use absolute path
            return str(file_path)
    
    def _get_file_stats(self, file_path: Path, content: str) -> Dict[str, Any]:
        """Get statistics about a file."""
        return {
            'language': self._detect_language(file_path.suffix),
            'size_bytes': len(content.encode('utf-8')),
            'line_count': len(content.split('\n'))
        }
    
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
        return ext_map.get(file_ext.lower(), 'unknown')
    
    def get_graph_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics about the code graph."""
        return {
            'files': self.db.get_files_summary(),
            'nodes': self.db.get_node_stats(),
            'relationships': self.db.get_relationship_stats()
        }
    
    def search_nodes(self, query: str, node_type: str = None) -> List[Dict[str, Any]]:
        """Search for nodes in the code graph."""
        if node_type:
            nodes = self.db.get_nodes_by_type(node_type)
            # Filter by query
            filtered_nodes = [
                node for node in nodes
                if query.lower() in node.name.lower() or 
                   (node.full_name and query.lower() in node.full_name.lower())
            ]
        else:
            filtered_nodes = self.db.search_nodes(query)
        
        return [
            {
                'id': node.id,
                'name': node.name,
                'full_name': node.full_name,
                'type': node.node_type,
                'file_path': node.file_path,
                'signature': node.signature,
                'start_line': node.start_line,
                'end_line': node.end_line,
                'metadata': node.metadata
            }
            for node in filtered_nodes
        ]
    
    def get_node_relationships(self, node_id: int) -> Dict[str, Any]:
        """Get all relationships for a node."""
        return {
            'outgoing': self.db.get_relationships_from_node(node_id),
            'incoming': self.db.get_relationships_to_node(node_id)
        }
    
    def get_function_call_graph(self) -> List[Dict[str, Any]]:
        """Get the function call graph."""
        return self.db.get_function_call_graph()
    
    def get_import_dependencies(self) -> List[Dict[str, Any]]:
        """Get import dependencies."""
        return self.db.get_import_dependencies()
    
    def get_class_hierarchy(self) -> List[Dict[str, Any]]:
        """Get class inheritance hierarchy."""
        return self.db.get_class_hierarchy()
    
    def close(self):
        """Close the database connection."""
        self.db.close()