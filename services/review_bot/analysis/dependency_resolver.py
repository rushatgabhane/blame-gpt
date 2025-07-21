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
            
            # Count how many impacts are in external files vs same file
            direct_external = len([i for i in impacts['direct'] if not self._is_same_file(i.get('file_path', ''), entity['file_path'])])
            secondary_external = len([i for i in impacts['secondary'] if not self._is_same_file(i.get('file_path', ''), entity['file_path'])])
            
            print(f"      Found {len(impacts['direct'])} direct impacts ({direct_external} external), "
                  f"{len(impacts['secondary'])} secondary impacts ({secondary_external} external)")
            print(f"      Same-file functions filtered out (whole file will be sent to LLM)")
        
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
        Uses enhanced function change detection if available.
        
        Args:
            mini_kg: Mini knowledge graph structure
            
        Returns:
            List of changed entities with metadata
        """
        changed_entities = []
        
        # First, check for enhanced function changes (line-level diff analysis)
        enhanced_function_changes = mini_kg.get("enhanced_function_changes", [])
        if enhanced_function_changes:
            print(f"   🎯 Using enhanced function changes: {len(enhanced_function_changes)} functions")
            for change in enhanced_function_changes:
                changed_entities.append({
                    "name": change["name"],
                    "file_path": change["file_path"],
                    "type": "function",
                    "change_type": change["change_type"],
                    "detection_method": "line_level_diff"
                })
        else:
            # Fallback to original logic
            print(f"   ⚠️ No enhanced function changes, falling back to original detection")
            
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
        
        # Only include file-level changes if we don't have enhanced function changes
        # This prevents duplicate analysis paths that create the same impacts
        if not enhanced_function_changes:
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
            
        # Store smart filtering results for comprehensive deduplication
        smart_filtering_results = []
        
        if entity["type"] == "file":
            # Find all files that import this file
            impacts["direct"].extend(self._find_file_importers(entity))
            
            # Find all functions in files that import this file (stored separately for deduplication)
            smart_filtering_results = self._find_transitive_function_impacts(entity)
        
        # Filter out same-file functions from impacts (but keep direct callers)
        entity_file = entity["file_path"]
        entity_name = entity["name"]
        impacts["direct"] = self._filter_out_same_file_functions_intelligently(impacts["direct"], entity_file, entity_name)
        
        # Comprehensive secondary impact collection with cross-source deduplication
        secondary_impacts_map = {}  # Use map to track unique impacts and prioritize function-level relationships
        
        # First collect smart filtering results from file analysis
        for smart_impact in smart_filtering_results:
            unique_key = f"{smart_impact.get('name', '')}:{smart_impact.get('file_path', '')}:{smart_impact.get('start_line', '')}"
            # Ensure smart filtering results have relationship_source for prioritization
            if "relationship_source" not in smart_impact:
                smart_impact["relationship_source"] = "file_import"
            secondary_impacts_map[unique_key] = smart_impact
        
        # Then collect any existing secondary impacts (for backward compatibility)
        for secondary_impact in impacts["secondary"]:
            unique_key = f"{secondary_impact.get('name', '')}:{secondary_impact.get('file_path', '')}:{secondary_impact.get('start_line', '')}"
            # Mark as file-level relationship for prioritization if not already marked
            if "relationship_source" not in secondary_impact:
                secondary_impact["relationship_source"] = "file_import"
            
            # Only add if not already present or if this has higher priority
            if unique_key not in secondary_impacts_map:
                secondary_impacts_map[unique_key] = secondary_impact
            else:
                current_priority = self._get_relationship_priority(secondary_impact)
                existing_priority = self._get_relationship_priority(secondary_impacts_map[unique_key])
                if current_priority < existing_priority:
                    secondary_impacts_map[unique_key] = secondary_impact
        
        # Then find secondary impacts from direct impacts (function-level relationships)
        for direct_impact in impacts["direct"]:
            if direct_impact["entity_type"] == "function":
                # Find callers of direct impacts (who calls the functions this function calls)
                secondary_callers = self._find_function_callers(direct_impact)
                
                for caller in secondary_callers:
                    unique_key = f"{caller.get('name', '')}:{caller.get('file_path', '')}:{caller.get('start_line', '')}"
                    # Mark as function-level relationship for prioritization
                    caller["relationship_source"] = "function_call"
                    
                    # Prioritize function-level over file-level relationships
                    if unique_key not in secondary_impacts_map or secondary_impacts_map[unique_key].get("relationship_source") == "file_import":
                        secondary_impacts_map[unique_key] = caller
                
                # Find callees of direct callees (what the called functions call)
                # This captures the complete call chain: changed_func -> direct_callee -> secondary_callee
                if direct_impact.get("relationship_type") == "called_by":
                    secondary_callees = self._find_function_callees(direct_impact)
                    
                    for callee in secondary_callees:
                        unique_key = f"{callee.get('name', '')}:{callee.get('file_path', '')}:{callee.get('start_line', '')}"
                        # Mark as function-level relationship for prioritization
                        callee["relationship_source"] = "function_call"
                        
                        # Prioritize function-level over file-level relationships
                        if unique_key not in secondary_impacts_map or secondary_impacts_map[unique_key].get("relationship_source") == "file_import":
                            secondary_impacts_map[unique_key] = callee
        
        # Convert back to list and filter out same-file functions
        impacts["secondary"] = list(secondary_impacts_map.values())
        impacts["secondary"] = self._filter_out_same_file_functions_intelligently(impacts["secondary"], entity_file, entity_name)
        
        # Final deduplication pass to handle smart filtering results
        # Smart filtering may have added additional entries that bypass our previous deduplication
        final_secondary_map = {}
        for impact in impacts["secondary"]:
            unique_key = f"{impact.get('name', '')}:{impact.get('file_path', '')}:{impact.get('start_line', '')}"
            
            # Prioritize by relationship source and filter reason
            should_replace = False
            if unique_key not in final_secondary_map:
                should_replace = True
            else:
                existing = final_secondary_map[unique_key]
                
                # Priority order: function_call > actual_usage > file_import
                current_priority = self._get_relationship_priority(impact)
                existing_priority = self._get_relationship_priority(existing)
                
                if current_priority < existing_priority:  # Lower number = higher priority
                    should_replace = True
            
            if should_replace:
                final_secondary_map[unique_key] = impact
        
        impacts["secondary"] = list(final_secondary_map.values())
        
        return impacts
    
    def _get_relationship_priority(self, impact: Dict[str, Any]) -> int:
        """
        Get priority order for relationship sources and filter reasons.
        Lower number = higher priority.
        
        Args:
            impact: Impact entity
            
        Returns:
            Priority level (lower is higher priority)
        """
        relationship_source = impact.get("relationship_source", "")
        filter_reason = impact.get("filter_reason", "")
        
        # Highest priority: Direct function calls
        if relationship_source == "function_call":
            return 1
        
        # Medium priority: Actual usage from smart filtering
        if filter_reason == "actual_usage":
            return 2
        
        # Lower priority: Other smart filtering reasons
        if filter_reason in ["high_centrality", "orchestrator"]:
            return 3
        
        # Lowest priority: File imports
        if relationship_source == "file_import":
            return 4
        
        # Default case
        return 5
    
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
            
            # Prioritize files by coupling strength - files with more calls are higher priority
            # This ensures we get complete coverage of the most tightly coupled files
            max_per_category = max(50, max_functions // 2)  # Increased limits to capture more functions
            
            # Separate functions by category
            actual_usage_functions = [f for f in filtered_functions if f.get('filter_reason') == 'actual_usage']
            high_centrality_functions = [f for f in filtered_functions if f.get('filter_reason') == 'high_centrality']
            orchestrator_functions = [f for f in filtered_functions if f.get('filter_reason') == 'orchestrator']
            
            # Simple and effective approach: prioritize files by number of calls to changed function
            def apply_file_priority_filtering(functions, limit):
                if len(functions) <= limit:
                    return functions
                
                # Group by file
                by_file = {}
                for func in functions:
                    file_path = func['file_path']
                    if file_path not in by_file:
                        by_file[file_path] = []
                    by_file[file_path].append(func)
                
                # Sort files by number of functions calling the changed code (descending)
                # Files with more calls are more tightly coupled and higher priority
                file_items = list(by_file.items())
                file_items.sort(key=lambda x: len(x[1]), reverse=True)
                
                result = []
                remaining_slots = limit
                
                # Take ALL functions from each file, starting with highest priority files
                for file_path, file_functions in file_items:
                    if remaining_slots <= 0:
                        break
                    
                    if len(file_functions) <= remaining_slots:
                        # Take all functions from this file
                        result.extend(file_functions)
                        remaining_slots -= len(file_functions)
                    else:
                        # Take as many as we can fit
                        result.extend(file_functions[:remaining_slots])
                        remaining_slots = 0
                        break
                
                return result
            
            # Apply file priority filtering to each category
            actual_usage_limited = apply_file_priority_filtering(actual_usage_functions, max_per_category)
            high_centrality_limited = apply_file_priority_filtering(high_centrality_functions, max_per_category)
            orchestrator_limited = apply_file_priority_filtering(orchestrator_functions, max_per_category)
            
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
                func.file_path as file_path,
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
            
            # Enhanced query to find both module calls and direct function calls via INVOKES
            module_name = entity["file_path"].split("/")[-1].replace(".ts", "").replace(".js", "")
            
            query = """
            // Find functions that call modules or have cross-file INVOKES relationships
            MATCH (caller_func:Function)
            WHERE NOT caller_func.file_path =~ ".*[Tt]est.*"
              AND NOT caller_func.file_path CONTAINS $module_name
              AND caller_func.file_path <> $file_path
            
            // Check for direct INVOKES relationships to target file functions
            OPTIONAL MATCH (caller_func)-[:INVOKES]->(target_func:Function)
            WHERE target_func.file_path ENDS WITH $file_path
            
            // Also check for module-style function calls
            OPTIONAL MATCH (caller_file:File)-[:CALLS]->(fc:FunctionCall)
            WHERE caller_file.path = caller_func.file_path
              AND (fc.target CONTAINS $module_name OR fc.target = $module_name)
              AND caller_func.start_line <= fc.line AND fc.line <= caller_func.end_line
            
            // Return functions that have either type of relationship
            WITH caller_func, target_func, fc
            WHERE target_func IS NOT NULL OR fc IS NOT NULL
            
            // Use a different approach: get a sample from each file
            WITH caller_func, target_func, fc
            WHERE target_func IS NOT NULL OR fc IS NOT NULL
            
            // Order by start_line first, then group by file and collect function data
            WITH caller_func, target_func, fc
            ORDER BY caller_func.file_path, caller_func.start_line
            
            // Group by file and collect function data in order
            WITH caller_func.file_path as file_path,
                 collect({
                     name: caller_func.name,
                     file_path: caller_func.file_path,
                     start_line: caller_func.start_line,
                     end_line: caller_func.end_line,
                     ast_type: caller_func.ast_type,
                     called_function: COALESCE(target_func.name, fc.target)
                 })[0..50] as functions  // Increased from 20 to 50 to capture more functions per file
            
            // Unwind to get individual functions back
            UNWIND functions as func
            
            RETURN DISTINCT
                func.name as func_name,
                func.file_path as file_path,
                func.start_line as start_line,
                func.end_line as end_line,
                func.ast_type as ast_type,
                func.called_function as called_function
            ORDER BY func.file_path, func.name
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
                func.file_path as file_path,
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
                func.file_path as file_path,
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
    
    def _filter_out_same_file_functions_intelligently(self, impacts: List[Dict[str, Any]], entity_file: str, entity_name: str) -> List[Dict[str, Any]]:
        """
        Intelligently filter same-file functions while preserving important call chains.
        
        KEEPS:
        1. All functions from different files
        2. Functions from same file that DIRECTLY CALL the changed function (important for call chains)
        3. Non-function entities (files, etc.)
        
        FILTERS OUT:
        1. Functions from same file that DON'T directly call the changed function (noise)
        
        Args:
            impacts: List of impact entities
            entity_file: File path of the changed entity
            entity_name: Name of the changed function
            
        Returns:
            Filtered list preserving important same-file callers
        """
        filtered_impacts = []
        
        for impact in impacts:
            should_keep = False
            
            # Always keep non-function entities (files, classes, etc.)
            if impact.get("entity_type") != "function":
                should_keep = True
            
            # Always keep functions from different files
            elif not self._is_same_file(impact.get("file_path", ""), entity_file):
                should_keep = True
            
            # For same-file functions: keep only if they directly call the changed function
            elif (self._is_same_file(impact.get("file_path", ""), entity_file) and 
                  impact.get("relationship_type") == "calls"):
                should_keep = True
                # Add metadata to indicate this is a same-file caller (for debugging)
                impact["same_file_caller"] = True
            
            if should_keep:
                filtered_impacts.append(impact)
        
        return filtered_impacts
    
    def _filter_out_same_file_functions(self, impacts: List[Dict[str, Any]], entity_file: str) -> List[Dict[str, Any]]:
        """
        LEGACY: Filter out functions that are in the same file as the changed entity.
        Since we'll send the whole changed file to the LLM anyway, 
        we don't need to list same-file functions as separate impacts.
        
        Args:
            impacts: List of impact entities
            entity_file: File path of the changed entity
            
        Returns:
            Filtered list excluding same-file functions
        """
        filtered_impacts = []
        
        for impact in impacts:
            # Keep the impact if:
            # 1. It's not a function (e.g., it's a file)
            # 2. It's a function in a different file
            if (impact.get("entity_type") != "function" or 
                not self._is_same_file(impact.get("file_path", ""), entity_file)):
                filtered_impacts.append(impact)
        
        return filtered_impacts
    
    def _is_same_file(self, impact_file: str, entity_file: str) -> bool:
        """
        Check if two file paths refer to the same file.
        Handles both relative and absolute paths.
        
        Args:
            impact_file: File path from impact entity
            entity_file: File path from changed entity
            
        Returns:
            True if they refer to the same file
        """
        if not impact_file or not entity_file:
            return False
        
        # Normalize paths by using the filename and comparing
        impact_filename = impact_file.split("/")[-1]
        entity_filename = entity_file.split("/")[-1]
        
        # Also check if one ends with the other (for relative vs absolute paths)
        return (impact_filename == entity_filename or 
                impact_file.endswith(entity_file) or 
                entity_file.endswith(impact_file) or
                impact_file == entity_file)
    
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