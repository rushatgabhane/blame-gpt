"""
Dependency Resolver - Queries the main knowledge graph to find entities impacted by PR changes.
This module takes the mini KG output and finds all dependencies using Neo4j queries.
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from libs.neo4j_client import Neo4jClient


class ImpactLevel(Enum):
    """Levels of impact for dependency analysis."""
    DIRECT = "direct"           # 1-hop: Direct callers/imports
    SECONDARY = "secondary"     # 2-hop: Secondary dependencies  
    TERTIARY = "tertiary"       # 3-hop: Tertiary dependencies


@dataclass
class ImpactedEntity:
    """Represents an entity impacted by changes."""
    name: str
    file_path: str
    entity_type: str  # function, class, file
    impact_level: ImpactLevel
    relationship_type: str  # calls, imports, contains, etc.
    start_line: Optional[int] = None
    end_line: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class DependencyChain:
    """Represents a chain of dependencies."""
    source_entity: str
    target_entity: str
    chain: List[str]
    impact_level: ImpactLevel


class DependencyResolver:
    """Resolves dependencies by querying the main knowledge graph."""
    
    def __init__(self, neo4j_client: Neo4jClient):
        """
        Initialize dependency resolver.
        
        Args:
            neo4j_client: Connected Neo4j client for querying main KG
        """
        self.neo4j_client = neo4j_client
        self.impacted_entities: List[ImpactedEntity] = []
        self.dependency_chains: List[DependencyChain] = []
        
    def analyze_dependencies(self, mini_kg: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze dependencies for all changes in the mini KG.
        
        Args:
            mini_kg: Mini knowledge graph from PR diff analyzer
            
        Returns:
            Structured dependency analysis results
        """
        print("🔗 Analyzing dependencies from main knowledge graph...")
        
        # Extract changed entities from mini KG
        changed_entities = self._extract_changed_entities(mini_kg)
        print(f"   Found {len(changed_entities)} changed entities to analyze")
        
        # Find impacted entities for each change
        all_impacts = {}
        
        for entity in changed_entities:
            print(f"   🔍 Analyzing impacts for: {entity['name']} ({entity['type']})")
            
            impacts = self._find_entity_impacts(entity)
            all_impacts[f"{entity['file_path']}:{entity['name']}"] = impacts
            
            print(f"      Found {len(impacts['direct'])} direct impacts, "
                  f"{len(impacts['secondary'])} secondary impacts")
        
        # Build dependency chains
        dependency_chains = self._build_dependency_chains(changed_entities, all_impacts)
        
        # Generate summary
        summary = self._generate_dependency_summary(all_impacts, dependency_chains)
        
        result = {
            "changed_entities": changed_entities,
            "impacts": all_impacts,
            "dependency_chains": dependency_chains,
            "summary": summary
        }
        
        print(f"✅ Dependency analysis complete!")
        print(f"   Total impacted entities: {summary['total_impacted']}")
        print(f"   Dependency chains: {len(dependency_chains)}")
        
        return result
    
    def _extract_changed_entities(self, mini_kg: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract changed entities from mini KG for dependency analysis.
        
        Args:
            mini_kg: Mini knowledge graph structure
            
        Returns:
            List of changed entities with metadata
        """
        changed_entities = []
        
        # Get function changes
        for change in mini_kg.get("changes", {}).get("added_functions", []):
            changed_entities.append({
                "name": change["name"],
                "file_path": change["file_path"],
                "type": "function",
                "change_type": "added"
            })
        
        for change in mini_kg.get("changes", {}).get("modified_functions", []):
            changed_entities.append({
                "name": change["name"],
                "file_path": change["file_path"],
                "type": "function",
                "change_type": "modified"
            })
        
        for change in mini_kg.get("changes", {}).get("deleted_functions", []):
            changed_entities.append({
                "name": change["name"],
                "file_path": change["file_path"],
                "type": "function",
                "change_type": "deleted"
            })
        
        # Get file changes
        for file_path in mini_kg.get("changes", {}).get("modified_files", []):
            changed_entities.append({
                "name": file_path.split("/")[-1],  # Just filename
                "file_path": file_path,
                "type": "file",
                "change_type": "modified"
            })
        
        return changed_entities
    
    def _find_entity_impacts(self, entity: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Find all entities impacted by a specific changed entity.
        
        Args:
            entity: Changed entity information
            
        Returns:
            Dictionary of impacts by level
        """
        impacts = {
            "direct": [],
            "secondary": [],
            "tertiary": []
        }
        
        if entity["type"] == "function":
            # Find functions that call this function
            impacts["direct"].extend(self._find_function_callers(entity))
            
            # Find functions this function calls (for context)
            impacts["direct"].extend(self._find_function_callees(entity))
            
            # Find files that import this function's file
            impacts["direct"].extend(self._find_file_importers(entity))
            
        elif entity["type"] == "file":
            # Find all files that import this file
            impacts["direct"].extend(self._find_file_importers(entity))
            
            # Find all functions in files that import this file
            impacts["secondary"].extend(self._find_transitive_function_impacts(entity))
        
        # Find secondary impacts (2-hop dependencies)
        for direct_impact in impacts["direct"]:
            if direct_impact["entity_type"] == "function":
                secondary_impacts = self._find_function_callers(direct_impact)
                impacts["secondary"].extend(secondary_impacts)
        
        return impacts
    
    def _find_function_callers(self, entity: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Find all functions that call the given function.
        
        Args:
            entity: Function entity to find callers for
            
        Returns:
            List of calling functions
        """
        if not self.neo4j_client.session:
            return []
        
        try:
            # Query to find functions that call this function
            # Handle both relative and absolute paths
            query = """
            MATCH (caller:Function)-[:CALLS|INVOKES]->(target:Function)
            WHERE target.name = $function_name 
            AND (target.file_path = $file_path OR target.file_path ENDS WITH $file_path)
            RETURN DISTINCT
                caller.name as caller_name,
                caller.file_path as caller_file,
                caller.start_line as start_line,
                caller.end_line as end_line,
                caller.ast_type as ast_type
            """
            
            result = self.neo4j_client.session.run(query, {
                "function_name": entity["name"],
                "file_path": entity["file_path"]
            })
            
            callers = []
            for record in result:
                callers.append({
                    "name": record["caller_name"],
                    "file_path": record["caller_file"],
                    "entity_type": "function",
                    "relationship_type": "calls",
                    "start_line": record["start_line"],
                    "end_line": record["end_line"],
                    "ast_type": record["ast_type"]
                })
            
            return callers
            
        except Exception as e:
            print(f"      ⚠️ Error finding function callers: {e}")
            return []
    
    def _find_function_callees(self, entity: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Find all functions that this function calls.
        
        Args:
            entity: Function entity to find callees for
            
        Returns:
            List of called functions
        """
        if not self.neo4j_client.session:
            return []
        
        try:
            # Query to find functions this function calls
            # Handle both relative and absolute paths
            query = """
            MATCH (caller:Function)-[:CALLS|INVOKES]->(target:Function)
            WHERE caller.name = $function_name 
            AND (caller.file_path = $file_path OR caller.file_path ENDS WITH $file_path)
            RETURN DISTINCT
                target.name as target_name,
                target.file_path as target_file,
                target.start_line as start_line,
                target.end_line as end_line,
                target.ast_type as ast_type
            """
            
            result = self.neo4j_client.session.run(query, {
                "function_name": entity["name"],
                "file_path": entity["file_path"]
            })
            
            callees = []
            for record in result:
                callees.append({
                    "name": record["target_name"],
                    "file_path": record["target_file"],
                    "entity_type": "function",
                    "relationship_type": "called_by",
                    "start_line": record["start_line"],
                    "end_line": record["end_line"],
                    "ast_type": record["ast_type"]
                })
            
            return callees
            
        except Exception as e:
            print(f"      ⚠️ Error finding function callees: {e}")
            return []
    
    def _find_file_importers(self, entity: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Find all files that import the given file.
        
        Args:
            entity: Entity with file_path to find importers for
            
        Returns:
            List of importing files
        """
        if not self.neo4j_client.session:
            return []
        
        try:
            # Query to find files that import this file
            # Handle both relative and absolute paths
            query = """
            MATCH (importer:File)-[:IMPORTS]->(target:File)
            WHERE target.path = $file_path OR target.path ENDS WITH $file_path
            RETURN DISTINCT
                importer.path as importer_path,
                importer.name as importer_name
            """
            
            result = self.neo4j_client.session.run(query, {
                "file_path": entity["file_path"]
            })
            
            importers = []
            for record in result:
                importers.append({
                    "name": record["importer_name"],
                    "file_path": record["importer_path"],
                    "entity_type": "file",
                    "relationship_type": "imports"
                })
            
            return importers
            
        except Exception as e:
            print(f"      ⚠️ Error finding file importers: {e}")
            return []
    
    def _find_transitive_function_impacts(self, entity: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Find functions in files that import the changed file.
        
        Args:
            entity: File entity to find transitive impacts for
            
        Returns:
            List of functions in importing files
        """
        if not self.neo4j_client.session:
            return []
        
        try:
            # Query to find functions in files that import this file
            # Handle both relative and absolute paths
            query = """
            MATCH (importer:File)-[:IMPORTS]->(target:File)-[:CONTAINS]->(func:Function)
            WHERE target.path = $file_path OR target.path ENDS WITH $file_path
            RETURN DISTINCT
                func.name as func_name,
                importer.path as file_path,
                func.start_line as start_line,
                func.end_line as end_line,
                func.ast_type as ast_type
            """
            
            result = self.neo4j_client.session.run(query, {
                "file_path": entity["file_path"]
            })
            
            functions = []
            for record in result:
                functions.append({
                    "name": record["func_name"],
                    "file_path": record["file_path"],
                    "entity_type": "function",
                    "relationship_type": "transitive_import",
                    "start_line": record["start_line"],
                    "end_line": record["end_line"],
                    "ast_type": record["ast_type"]
                })
            
            return functions
            
        except Exception as e:
            print(f"      ⚠️ Error finding transitive function impacts: {e}")
            return []
    
    def _build_dependency_chains(
        self, 
        changed_entities: List[Dict[str, Any]], 
        impacts: Dict[str, Dict[str, List[Dict[str, Any]]]]
    ) -> List[Dict[str, Any]]:
        """
        Build dependency chains showing how changes propagate.
        
        Args:
            changed_entities: List of changed entities
            impacts: Impact analysis results
            
        Returns:
            List of dependency chains
        """
        chains = []
        
        for entity in changed_entities:
            entity_key = f"{entity['file_path']}:{entity['name']}"
            entity_impacts = impacts.get(entity_key, {})
            
            # Build chains for direct impacts
            for impact in entity_impacts.get("direct", []):
                chain = {
                    "source": entity["name"],
                    "source_file": entity["file_path"],
                    "target": impact["name"],
                    "target_file": impact["file_path"],
                    "relationship": impact["relationship_type"],
                    "length": 1,
                    "risk_level": self._assess_risk_level(entity, impact)
                }
                chains.append(chain)
            
            # Build chains for secondary impacts
            for impact in entity_impacts.get("secondary", []):
                chain = {
                    "source": entity["name"],
                    "source_file": entity["file_path"],
                    "target": impact["name"],
                    "target_file": impact["file_path"],
                    "relationship": impact["relationship_type"],
                    "length": 2,
                    "risk_level": self._assess_risk_level(entity, impact)
                }
                chains.append(chain)
        
        return chains
    
    def _assess_risk_level(self, source: Dict[str, Any], target: Dict[str, Any]) -> str:
        """
        Assess the risk level of a dependency relationship.
        
        Args:
            source: Source entity
            target: Target entity
            
        Returns:
            Risk level string
        """
        # Simple risk assessment based on change type and relationship
        if source.get("change_type") == "deleted":
            return "high"
        elif source.get("change_type") == "modified":
            if target.get("relationship_type") == "calls":
                return "medium"
            else:
                return "low"
        else:  # added
            return "low"
    
    def _generate_dependency_summary(
        self, 
        impacts: Dict[str, Dict[str, List[Dict[str, Any]]]], 
        chains: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate summary statistics for dependency analysis.
        
        Args:
            impacts: Impact analysis results
            chains: Dependency chains
            
        Returns:
            Summary statistics
        """
        total_direct = sum(len(entity_impacts.get("direct", [])) for entity_impacts in impacts.values())
        total_secondary = sum(len(entity_impacts.get("secondary", [])) for entity_impacts in impacts.values())
        total_tertiary = sum(len(entity_impacts.get("tertiary", [])) for entity_impacts in impacts.values())
        
        # Count by entity type
        entity_counts = {"function": 0, "file": 0, "class": 0}
        for entity_impacts in impacts.values():
            for level_impacts in entity_impacts.values():
                for impact in level_impacts:
                    entity_type = impact.get("entity_type", "unknown")
                    if entity_type in entity_counts:
                        entity_counts[entity_type] += 1
        
        # Count by risk level
        risk_counts = {"high": 0, "medium": 0, "low": 0}
        for chain in chains:
            risk_level = chain.get("risk_level", "low")
            if risk_level in risk_counts:
                risk_counts[risk_level] += 1
        
        return {
            "total_impacted": total_direct + total_secondary + total_tertiary,
            "direct_impacts": total_direct,
            "secondary_impacts": total_secondary,
            "tertiary_impacts": total_tertiary,
            "entity_counts": entity_counts,
            "risk_counts": risk_counts,
            "dependency_chains": len(chains)
        }