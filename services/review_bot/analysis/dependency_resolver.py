"""
Dependency Resolver - Queries the main knowledge graph to find entities impacted by PR changes.
This module takes the mini KG output and finds all dependencies using Neo4j queries.
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from libs.neo4j_client import Neo4jClient
from services.review_bot.config import ReviewBotConfig


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
        self.smart_filtering_config = ReviewBotConfig.get_smart_filtering_config()
        
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
        Find functions in files that import the changed file, with smart filtering.
        
        Args:
            entity: File entity to find transitive impacts for
            
        Returns:
            List of functions in importing files (filtered for relevance)
        """
        if not self.neo4j_client.session:
            return []
        
        try:
            # Check if smart filtering is enabled
            if not self.smart_filtering_config["enabled"]:
                return self._find_all_transitive_functions(entity)
            
            # Strategy 1: Find functions that actually use the changed code
            actual_usage_functions = self._find_actual_usage_functions(entity)
            
            # Strategy 2: Find high-centrality functions (called by many others)
            high_centrality_functions = self._find_high_centrality_functions(entity)
            
            # Strategy 3: Find functions that call many others (potential orchestrators)
            orchestrator_functions = self._find_orchestrator_functions(entity)
            
            # Combine and deduplicate results
            all_functions = {}
            
            # Priority 1: Actual usage (highest priority)
            for func in actual_usage_functions:
                key = f"{func['file_path']}:{func['name']}"
                func['filter_reason'] = 'actual_usage'
                func['priority'] = 1
                all_functions[key] = func
            
            # Priority 2: High centrality
            for func in high_centrality_functions:
                key = f"{func['file_path']}:{func['name']}"
                if key not in all_functions:
                    func['filter_reason'] = 'high_centrality'
                    func['priority'] = 2
                    all_functions[key] = func
            
            # Priority 3: Orchestrators
            for func in orchestrator_functions:
                key = f"{func['file_path']}:{func['name']}"
                if key not in all_functions:
                    func['filter_reason'] = 'orchestrator'
                    func['priority'] = 3
                    all_functions[key] = func
            
            # Convert back to list and sort by priority
            filtered_functions = list(all_functions.values())
            filtered_functions.sort(key=lambda x: x['priority'])
            
            # Cap at configured max functions to prevent overwhelming results
            max_functions = self.smart_filtering_config["max_secondary_impacts"]
            
            # Also apply per-category limits to ensure diversity
            max_per_category = max(10, max_functions // 3)
            
            # Limit each category
            actual_usage_limited = [f for f in filtered_functions if f.get('filter_reason') == 'actual_usage'][:max_per_category]
            high_centrality_limited = [f for f in filtered_functions if f.get('filter_reason') == 'high_centrality'][:max_per_category]
            orchestrator_limited = [f for f in filtered_functions if f.get('filter_reason') == 'orchestrator'][:max_per_category]
            
            # Combine limited results
            filtered_functions = actual_usage_limited + high_centrality_limited + orchestrator_limited
            
            if len(filtered_functions) > max_functions:
                print(f"      📊 Smart filtering: {len(all_functions)} → {max_functions} functions")
                filtered_functions = filtered_functions[:max_functions]
            else:
                print(f"      📊 Smart filtering: Found {len(filtered_functions)} relevant functions")
            
            return filtered_functions
            
        except Exception as e:
            print(f"      ⚠️ Error finding transitive function impacts: {e}")
            return []
    
    def _find_all_transitive_functions(self, entity: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Find ALL functions in files that import the changed file (original approach).
        
        Args:
            entity: File entity to find transitive impacts for
            
        Returns:
            List of ALL functions in importing files (unfiltered)
        """
        if not self.neo4j_client.session:
            return []
        
        try:
            # Original query - returns ALL functions in importing files
            query = """
            MATCH (importer:File)-[:IMPORTS]->(target:File)
            WHERE target.path = $file_path OR target.path ENDS WITH $file_path
            MATCH (importer)-[:CONTAINS]->(func:Function)
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
                    "ast_type": record["ast_type"],
                    "filter_reason": "no_filtering",
                    "priority": 1
                })
            
            print(f"      📊 No filtering: Found {len(functions)} functions")
            return functions
            
        except Exception as e:
            print(f"      ⚠️ Error finding all transitive functions: {e}")
            return []
    
    def _find_actual_usage_functions(self, entity: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Find functions that actually call functions from the changed file.
        
        Args:
            entity: File entity to analyze
            
        Returns:
            List of functions that actually use the changed code
        """
        if not self.neo4j_client.session:
            return []
        
        try:
            print(f"      🔍 Looking for actual usage of: {entity['file_path']}")
            
            # Fixed query - simplified approach that actually works
            # Look for function calls that reference the changed module
            module_name = entity["file_path"].split("/")[-1].replace(".ts", "").replace(".js", "")
            
            query = """
            MATCH (caller_file:File)-[:CALLS]->(fc:FunctionCall)
            WHERE (fc.target CONTAINS $module_name
                   OR fc.target = $module_name)
              AND NOT caller_file.path =~ ".*[Tt]est.*"
              AND NOT caller_file.path CONTAINS $module_name
              AND caller_file.path <> $file_path
            
            MATCH (caller_file)-[:CONTAINS]->(caller_func:Function)
            
            // Check if the call is within the function's line range
            WHERE caller_func.start_line <= fc.line AND fc.line <= caller_func.end_line
            
            RETURN DISTINCT
                caller_func.name as func_name,
                caller_file.path as file_path,
                caller_func.start_line as start_line,
                caller_func.end_line as end_line,
                caller_func.ast_type as ast_type,
                fc.target as called_function
            LIMIT 30
            """
            
            result = self.neo4j_client.session.run(query, {
                "file_path": entity["file_path"],
                "module_name": module_name
            })
            
            functions = []
            for record in result:
                functions.append({
                    "name": record["func_name"],
                    "file_path": record["file_path"],
                    "entity_type": "function",
                    "relationship_type": "actual_usage",
                    "start_line": record["start_line"],
                    "end_line": record["end_line"],
                    "ast_type": record["ast_type"],
                    "called_function": record["called_function"]
                })
            
            print(f"      ✅ Found {len(functions)} functions with actual usage")
            
            # Debug: Show sample calls
            for func in functions[:3]:
                print(f"         - {func['name']} calls {func['called_function']}")
            
            return functions
            
        except Exception as e:
            print(f"      ⚠️ Error finding actual usage functions: {e}")
            return []
    
    def _find_high_centrality_functions(self, entity: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Find functions with high centrality (called by many others) in importing files.
        
        Args:
            entity: File entity to analyze
            
        Returns:
            List of high-centrality functions
        """
        if not self.neo4j_client.session:
            return []
        
        try:
            print(f"      🔍 Looking for high centrality functions in files importing: {entity['file_path']}")
            
            # Query to find functions that are called by many others
            query = """
            MATCH (target_file:File)<-[:IMPORTS]-(importer:File)
            WHERE target_file.path ENDS WITH $file_path
            AND NOT importer.path =~ ".*Test.*"
            AND NOT importer.path =~ ".*test.*"
            
            MATCH (importer)-[:CONTAINS]->(func:Function)
            WHERE func.file_path = importer.path
            
            // Count incoming calls - using FunctionCall pattern
            OPTIONAL MATCH (caller_file:File)-[:CALLS]->(fc:FunctionCall)
            WHERE fc.target = func.name AND caller_file.path <> importer.path
            WITH func, importer, count(fc) as incoming_calls
            WHERE incoming_calls >= $min_centrality
            
            RETURN DISTINCT
                func.name as func_name,
                importer.path as file_path,
                func.start_line as start_line,
                func.end_line as end_line,
                func.ast_type as ast_type,
                incoming_calls
            ORDER BY incoming_calls DESC
            LIMIT 20
            """
            
            result = self.neo4j_client.session.run(query, {
                "file_path": entity["file_path"],
                "min_centrality": self.smart_filtering_config["min_centrality_threshold"]
            })
            
            functions = []
            for record in result:
                functions.append({
                    "name": record["func_name"],
                    "file_path": record["file_path"],
                    "entity_type": "function",
                    "relationship_type": "high_centrality",
                    "start_line": record["start_line"],
                    "end_line": record["end_line"],
                    "ast_type": record["ast_type"],
                    "incoming_calls": record["incoming_calls"]
                })
            
            print(f"      ✅ Found {len(functions)} high centrality functions")
            
            # Debug: Show sample functions
            for func in functions[:3]:
                print(f"         - {func['name']} ({func['incoming_calls']} incoming calls)")
            
            return functions
            
        except Exception as e:
            print(f"      ⚠️ Error finding high centrality functions: {e}")
            return []
    
    def _find_orchestrator_functions(self, entity: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Find functions that call many others (orchestrators) in importing files.
        
        Args:
            entity: File entity to analyze
            
        Returns:
            List of orchestrator functions
        """
        if not self.neo4j_client.session:
            return []
        
        try:
            print(f"      🔍 Looking for orchestrator functions in files importing: {entity['file_path']}")
            
            # Query to find functions that call many others
            query = """
            MATCH (target_file:File)<-[:IMPORTS]-(importer:File)
            WHERE target_file.path ENDS WITH $file_path
            AND NOT importer.path =~ ".*Test.*"
            AND NOT importer.path =~ ".*test.*"
            AND NOT importer.path =~ ".*/utils/.*"
            
            MATCH (importer)-[:CONTAINS]->(func:Function)
            WHERE func.file_path = importer.path
            
            // Count outgoing calls - using FunctionCall pattern
            OPTIONAL MATCH (importer)-[:CALLS]->(fc:FunctionCall)
            WHERE func.start_line <= fc.line AND fc.line <= func.end_line
            WITH func, importer, count(fc) as outgoing_calls
            WHERE outgoing_calls >= $min_orchestrator
            
            RETURN DISTINCT
                func.name as func_name,
                importer.path as file_path,
                func.start_line as start_line,
                func.end_line as end_line,
                func.ast_type as ast_type,
                outgoing_calls
            ORDER BY outgoing_calls DESC
            LIMIT 20
            """
            
            result = self.neo4j_client.session.run(query, {
                "file_path": entity["file_path"],
                "min_orchestrator": self.smart_filtering_config["min_orchestrator_threshold"]
            })
            
            functions = []
            for record in result:
                functions.append({
                    "name": record["func_name"],
                    "file_path": record["file_path"],
                    "entity_type": "function",
                    "relationship_type": "orchestrator",
                    "start_line": record["start_line"],
                    "end_line": record["end_line"],
                    "ast_type": record["ast_type"],
                    "outgoing_calls": record["outgoing_calls"]
                })
            
            print(f"      ✅ Found {len(functions)} orchestrator functions")
            
            # Debug: Show sample functions
            for func in functions[:3]:
                print(f"         - {func['name']} ({func['outgoing_calls']} outgoing calls)")
            
            return functions
            
        except Exception as e:
            print(f"      ⚠️ Error finding orchestrator functions: {e}")
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