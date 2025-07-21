"""
Neo4j client for managing knowledge graph operations.
Handles database connections, schema initialization, and bulk data loading.
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from neo4j import GraphDatabase, basic_auth


class Neo4jClient:
    def __init__(self, uri: str = "bolt://localhost:7687", user: str = "neo4j", password: str = "password"):
        """
        Initialize Neo4j client.
        
        Args:
            uri: Neo4j connection URI
            user: Neo4j username
            password: Neo4j password
        """
        self.uri = uri
        self.user = user
        self.password = password
        self.driver = None
        self.session = None

    def connect(self) -> Tuple[bool, str]:
        """
        Connect to Neo4j database.
        
        Returns:
            Tuple of (success, message)
        """
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=basic_auth(self.user, self.password))
            self.session = self.driver.session()
            
            # Test connection
            result = self.session.run("RETURN 'connected' AS message")
            message = result.single()["message"]
            
            return True, f"Connected to Neo4j: {message}"
        except Exception as e:
            return False, f"Failed to connect to Neo4j: {str(e)}"

    def disconnect(self):
        """Close Neo4j connection."""
        if self.session:
            self.session.close()
        if self.driver:
            self.driver.close()

    def init_schema(self) -> bool:
        """
        Initialize the Neo4j schema with constraints and indexes.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Clear existing data
            self.session.run("MATCH (n) DETACH DELETE n")

            # Drop old constraints if they exist
            constraint_names = [
                "file_path_unique",
                "function_unique", 
                "class_unique",
                "variable_unique"
            ]
            
            for name in constraint_names:
                self.session.run(f"DROP CONSTRAINT {name} IF EXISTS")

            # Create constraints
            constraints = [
                """
                CREATE CONSTRAINT file_path_unique
                FOR (f:File) REQUIRE f.path IS UNIQUE
                """,
                """
                CREATE CONSTRAINT function_unique
                FOR (f:Function) REQUIRE (f.file_path, f.name, f.start_line) IS UNIQUE
                """,
                """
                CREATE CONSTRAINT class_unique
                FOR (c:Class) REQUIRE (c.file_path, c.name, c.start_line) IS UNIQUE
                """,
                """
                CREATE CONSTRAINT variable_unique
                FOR (v:Variable) REQUIRE (v.file_path, v.name, v.start_line) IS UNIQUE
                """
            ]

            for constraint in constraints:
                self.session.run(constraint)

            return True
        except Exception as e:
            print(f"Error initializing schema: {e}")
            return False

    def load_files(self, analyses: List[Dict[str, Any]], repo_dir: Path) -> int:
        """
        Load file nodes into Neo4j.
        
        Args:
            analyses: List of file analysis results
            repo_dir: Repository root directory
            
        Returns:
            Number of files loaded
        """
        rows = []
        for analysis in analyses:
            if not analysis["success"]:
                continue
                
            file_path = Path(analysis["file_path"]).resolve()
            
            try:
                stat = file_path.stat()
                relative_path = str(file_path.relative_to(repo_dir))
            except (OSError, ValueError):
                continue
                
            rows.append({
                'path': str(file_path),
                'name': file_path.name,
                'rel': relative_path,
                'ext': file_path.suffix,
                'size': stat.st_size,
                'tot': analysis["total_entities"],
                'fc': len(analysis["functions"]),
                'cc': len(analysis["classes"]),
                'vc': len(analysis["variables"]),
                'ic': len(analysis["imports"]),
                'ec': len(analysis["exports"]),
                'calls': len(analysis["function_calls"])
            })

        if rows:
            self.session.run("""
            UNWIND $rows AS r
            MERGE (f:File {path: r.path})
            SET f += {
                name: r.name,
                relative_path: r.rel,
                extension: r.ext,
                size_bytes: r.size,
                total_entities: r.tot,
                function_count: r.fc,
                class_count: r.cc,
                variable_count: r.vc,
                import_count: r.ic,
                export_count: r.ec,
                function_call_count: r.calls
            }
            """, rows=rows)

        return len(rows)

    def load_entities(self, analyses: List[Dict[str, Any]]) -> Tuple[int, int, int]:
        """
        Load entity nodes (functions, classes, variables) into Neo4j.
        
        Args:
            analyses: List of file analysis results
            
        Returns:
            Tuple of (functions_count, classes_count, variables_count)
        """
        function_rows = []
        class_rows = []
        variable_rows = []

        for analysis in analyses:
            if not analysis["success"]:
                continue
                
            file_path = analysis["file_path"]
            
            # Add file_path to each entity
            for entity in analysis["functions"]:
                function_rows.append({**entity, "file_path": file_path})
            
            for entity in analysis["classes"]:
                class_rows.append({**entity, "file_path": file_path})
                
            for entity in analysis["variables"]:
                variable_rows.append({**entity, "file_path": file_path})

        # Load functions
        if function_rows:
            self.session.run("""
            UNWIND $rows AS r
            MERGE (fn:Function {file_path: r.file_path, name: r.name, start_line: r.start_line})
            SET fn += r
            """, rows=function_rows)

        # Load classes
        if class_rows:
            self.session.run("""
            UNWIND $rows AS r
            MERGE (cl:Class {file_path: r.file_path, name: r.name, start_line: r.start_line})
            SET cl += r
            """, rows=class_rows)

        # Load variables
        if variable_rows:
            self.session.run("""
            UNWIND $rows AS r
            MERGE (vr:Variable {file_path: r.file_path, name: r.name, start_line: r.start_line})
            SET vr += r
            """, rows=variable_rows)

        return len(function_rows), len(class_rows), len(variable_rows)

    def load_contains_relationships(self, analyses: List[Dict[str, Any]]) -> int:
        """
        Load CONTAINS relationships between files and entities.
        
        Args:
            analyses: List of file analysis results
            
        Returns:
            Number of relationships created
        """
        relationships = []
        
        for analysis in analyses:
            if not analysis["success"]:
                continue
                
            file_path = analysis["file_path"]
            
            # Add all entities
            for entity_list, entity_type in [
                (analysis["functions"], "function"),
                (analysis["classes"], "class"),
                (analysis["variables"], "variable")
            ]:
                for entity in entity_list:
                    relationships.append({
                        "file_path": file_path,
                        "name": entity["name"],
                        "line": entity["start_line"],
                        "etype": entity_type
                    })

        if relationships:
            self.session.run("""
            UNWIND $rows AS r
            MATCH (f:File {path: r.file_path})
            MATCH (e {file_path: r.file_path, name: r.name, start_line: r.line})
            MERGE (f)-[:CONTAINS {entity_type: r.etype}]->(e)
            """, rows=relationships)

        return len(relationships)

    def load_import_relationships(self, file_rels: List[Dict[str, Any]]) -> Tuple[int, int]:
        """
        Load import relationships between files and external modules.
        
        Args:
            file_rels: List of file relationship dictionaries
            
        Returns:
            Tuple of (internal_imports, external_imports)
        """
        internal_rows = []
        external_rows = []

        for rel in file_rels:
            if rel["type"] == "imports":
                internal_rows.append({
                    "src": rel["source_file"],
                    "tgt": rel["target_file"],
                    "line": rel["import_line"],
                    "stmt": rel["import_stmt"],
                    "alias": json.dumps(rel["alias_map"])
                })
            elif rel["type"] == "external_import":
                external_rows.append({
                    "src": rel["source_file"],
                    "mod": rel["target_module"],
                    "line": rel["import_line"],
                    "stmt": rel["import_stmt"],
                    "alias": json.dumps(rel["alias_map"])
                })

        # Load internal imports
        if internal_rows:
            self.session.run("""
            UNWIND $rows AS r
            MATCH (s:File {path: r.src})
            MATCH (t:File {path: r.tgt})
            MERGE (s)-[:IMPORTS {line: r.line, stmt: r.stmt, alias_map: r.alias}]->(t)
            """, rows=internal_rows)

        # Load external imports
        if external_rows:
            self.session.run("""
            UNWIND $rows AS r
            MERGE (m:ExternalModule {name: r.mod})
            WITH m, r
            MATCH (s:File {path: r.src})
            MERGE (s)-[:IMPORTS_EXTERNAL {line: r.line, stmt: r.stmt, alias_map: r.alias}]->(m)
            """, rows=external_rows)

        return len(internal_rows), len(external_rows)

    def load_function_call_relationships(self, call_rels: List[Dict[str, Any]]) -> int:
        """
        Load function call relationships.
        
        Args:
            call_rels: List of function call relationship dictionaries
            
        Returns:
            Number of function call nodes created
        """
        rows = []
        
        for rel in call_rels:
            if rel["call_type"] == "direct_call":
                target = rel["target_function"]
            else:  # method_call
                target = f"{rel['target_object']}.{rel['target_method']}"
                
            rows.append({
                "src": rel["source_file"],
                "line": rel["line"],
                "target": target,
                "ctype": rel["call_type"]
            })

        if rows:
            self.session.run("""
            UNWIND $rows AS r
            MATCH (f:File {path: r.src})
            MERGE (f)-[:CALLS]->(c:FunctionCall {
                file_path: r.src,
                line: r.line,
                target: r.target
            })
            SET c.call_type = r.ctype
            """, rows=rows)

        return len(rows)

    def resolve_same_file_calls(self) -> bool:
        """
        Create INVOKES relationships for same-file function calls.
        
        Returns:
            True if successful
        """
        try:
            self.session.run("""
            MATCH (file:File)-[:CALLS]->(fc:FunctionCall)
            MATCH (file)-[:CONTAINS]->(caller:Function)
            MATCH (file)-[:CONTAINS]->(target:Function)
            WHERE fc.target = target.name
              AND caller.start_line <= fc.line 
              AND fc.line <= caller.end_line
              AND caller.name <> target.name
            MERGE (caller)-[:INVOKES]->(target)
            """)
            return True
        except Exception as e:
            print(f"Error resolving same-file calls: {e}")
            return False

    def load_cross_file_call_relationships(self, cross_file_rels: List[Dict[str, Any]]) -> int:
        """
        Load cross-file function call relationships and create INVOKES relationships.
        
        Args:
            cross_file_rels: List of cross-file call relationship dictionaries
            
        Returns:
            Number of INVOKES relationships created
        """
        if not cross_file_rels:
            return 0
            
        rows = []
        for rel in cross_file_rels:
            rows.append({
                "source_file": rel["source_file"],
                "target_file": rel["target_file"],
                "function_name": rel["function_name"],
                "line": rel["line"]
            })

        if rows:
            result = self.session.run("""
            UNWIND $rows AS r
            MATCH (source_func:Function)
            WHERE source_func.file_path = r.source_file
              AND source_func.start_line <= r.line 
              AND r.line <= source_func.end_line
            MATCH (target_func:Function)
            WHERE target_func.file_path = r.target_file
              AND target_func.name = r.function_name
            MERGE (source_func)-[:INVOKES]->(target_func)
            RETURN count(*) as relationships_created
            """, rows=rows)
            
            count = result.single()
            return count["relationships_created"] if count else 0
        
        return 0

    def get_stats(self) -> Dict[str, Any]:
        """
        Get knowledge graph statistics.
        
        Returns:
            Dictionary with node and relationship counts
        """
        try:
            # Node counts
            node_result = self.session.run("""
            MATCH (n)
            RETURN labels(n) as labels, count(n) as count
            ORDER BY count DESC
            """)
            
            nodes = {str(record['labels']): record['count'] for record in node_result}
            
            # Relationship counts
            rel_result = self.session.run("""
            MATCH ()-[r]->()
            RETURN type(r) as relationship_type, count(r) as count
            ORDER BY count DESC
            """)
            
            relationships = {record['relationship_type']: record['count'] for record in rel_result}
            
            return {
                'nodes': nodes,
                'relationships': relationships,
                'total_nodes': sum(nodes.values()),
                'total_relationships': sum(relationships.values())
            }
        except Exception as e:
            print(f"Error getting stats: {e}")
            return {}

    def query(self, cypher: str, parameters: Optional[Dict] = None) -> List[Dict]:
        """
        Execute a Cypher query.
        
        Args:
            cypher: Cypher query string
            parameters: Query parameters
            
        Returns:
            List of result records as dictionaries
        """
        try:
            result = self.session.run(cypher, parameters or {})
            return [dict(record) for record in result]
        except Exception as e:
            print(f"Query error: {e}")
            return []