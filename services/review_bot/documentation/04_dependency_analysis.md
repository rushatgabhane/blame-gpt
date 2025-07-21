# Dependency Analysis Documentation

## Overview

The dependency analysis component identifies all code entities that could be affected by changes in a pull request. It queries the main knowledge graph to trace dependencies and uses smart filtering to provide relevant results.

## Core Concepts

### Impact Levels

1. **Direct Impact** (1-hop)
   - Functions that directly call changed functions
   - Files that directly import changed files
   - Functions that the changed function calls

2. **Secondary Impact** (2-hop)
   - Functions that call the direct impact functions
   - Functions in files that import files with direct impacts
   - Extended call chains

3. **Tertiary Impact** (3-hop)
   - Further propagation (usually filtered out)

### Relationship Types

The system tracks different types of dependencies:
- **calls**: Function A calls function B
- **imports**: File A imports file B
- **contains**: File contains function/class/variable
- **invokes**: Cross-file function invocation
- **transitive_import**: Functions in importing files

## Dependency Resolution Process

```
1. Extract Changed Entities
        ↓
2. Query Direct Dependencies
        ↓
3. Query Secondary Dependencies
        ↓
4. Apply Intelligent Same-File Filtering
        ↓
5. Apply Smart Filtering (Secondary Only)
        ↓
6. Build Dependency Chains
        ↓
7. Generate Impact Report
```

## Implementation Details

### 1. Changed Entity Extraction

The system prioritizes enhanced function changes when available:

```python
def _extract_changed_entities(mini_kg):
    # Priority 1: Enhanced function changes (line-level)
    enhanced_changes = mini_kg.get("enhanced_function_changes", [])
    if enhanced_changes:
        # Use precise line-level detection
        return process_enhanced_changes(enhanced_changes)
    
    # Fallback: Traditional detection
    return process_traditional_changes(mini_kg)
```

### 2. Direct Impact Queries

#### Finding Function Callers
```cypher
MATCH (caller:Function)-[:CALLS|INVOKES]->(target:Function)
WHERE target.name = $function_name 
  AND target.file_path ENDS WITH $file_path
RETURN DISTINCT
    caller.name as caller_name,
    caller.file_path as caller_file,
    caller.start_line as start_line
```

#### Finding File Importers
```cypher
MATCH (importer:File)-[:IMPORTS]->(target:File)
WHERE target.path ENDS WITH $file_path
RETURN DISTINCT
    importer.path as importer_path,
    importer.name as importer_name
```

### 3. Intelligent Same-File Function Filtering

The system uses intelligent filtering to preserve important call chains while reducing noise:

```python
def _filter_out_same_file_functions_intelligently(impacts, entity_file, entity_name):
    # KEEPS:
    # 1. All functions from different files
    # 2. Functions from same file that DIRECTLY CALL the changed function (important for call chains)
    # 3. Non-function entities (files, etc.)
    
    # FILTERS OUT:
    # 1. Functions from same file that DON'T directly call the changed function (noise)
    
    filtered = []
    for impact in impacts:
        should_keep = False
        
        # Always keep non-function entities
        if impact["entity_type"] != "function":
            should_keep = True
        
        # Always keep functions from different files
        elif not is_same_file(impact["file_path"], entity_file):
            should_keep = True
        
        # For same-file functions: keep only if they directly call the changed function
        elif (is_same_file(impact["file_path"], entity_file) and 
              impact["relationship_type"] == "calls"):
            should_keep = True
            impact["same_file_caller"] = True  # Mark for debugging
        
        if should_keep:
            filtered.append(impact)
    
    return filtered
```

**Rationale**: Preserves complete dependency chains by keeping same-file functions that directly call the changed function, while still filtering out unrelated same-file functions to reduce noise.

### 4. Smart Filtering Strategies

After intelligent same-file filtering, the system implements three filtering strategies for secondary impacts to reduce noise:

#### Strategy 1: Actual Usage Detection
Finds functions that actually use the changed code:

```cypher
// Find functions with actual INVOKES relationships
MATCH (caller:Function)-[:INVOKES]->(target:Function)
WHERE target.file_path ENDS WITH $file_path

// Or module-style function calls
MATCH (caller_file:File)-[:CALLS]->(fc:FunctionCall)
WHERE fc.target CONTAINS $module_name
  AND caller_func.start_line <= fc.line 
  AND fc.line <= caller_func.end_line
```

**Priority**: Highest - These are confirmed dependencies

#### Strategy 2: High Centrality Functions
Identifies important functions called by many others:

```cypher
MATCH (func:Function)
OPTIONAL MATCH (caller)-[:CALLS]->(fc:FunctionCall)
WHERE fc.target = func.name
WITH func, count(fc) as incoming_calls
WHERE incoming_calls >= $min_centrality_threshold
```

**Threshold**: Default 5 incoming calls
**Rationale**: Central functions are likely important for testing

#### Strategy 3: Orchestrator Functions
Finds functions that coordinate many operations:

```cypher
MATCH (func:Function)
OPTIONAL MATCH (file)-[:CALLS]->(fc:FunctionCall)
WHERE func.start_line <= fc.line 
  AND fc.line <= func.end_line
WITH func, count(fc) as outgoing_calls
WHERE outgoing_calls >= $min_orchestrator_threshold
```

**Threshold**: Default 10 outgoing calls
**Rationale**: Orchestrators may use changed functionality

### 4. File Priority Filtering

When multiple functions are found, the system prioritizes by file coupling:

```python
def apply_file_priority_filtering(functions, limit):
    # Group functions by file
    by_file = group_by_file(functions)
    
    # Sort files by coupling strength (number of functions)
    file_items = sorted(by_file.items(), 
                       key=lambda x: len(x[1]), 
                       reverse=True)
    
    # Take all functions from high-priority files first
    result = []
    for file_path, file_functions in file_items:
        if len(result) + len(file_functions) <= limit:
            result.extend(file_functions)
        else:
            # Take what we can fit
            remaining = limit - len(result)
            result.extend(file_functions[:remaining])
            break
    
    return result
```

## Configuration

Smart filtering is configured via environment variables:

```python
# Enable/disable smart filtering
ENABLE_SMART_FILTERING = "true"

# Maximum secondary impacts to return
MAX_SECONDARY_IMPACTS = 80

# Minimum incoming calls for high centrality
MIN_CENTRALITY_THRESHOLD = 5

# Minimum outgoing calls for orchestrators
MIN_ORCHESTRATOR_THRESHOLD = 10
```

## Example Analysis

### Input: Changed Function
```python
{
    "name": "getReportNameInternal",
    "file_path": "src/libs/ReportUtils.ts",
    "change_type": "modified"
}
```

### Output: Dependency Analysis (with Intelligent Filtering)
```json
{
  "changed_entities": [
    {
      "name": "getReportNameInternal",
      "file_path": "src/libs/ReportUtils.ts",
      "type": "function",
      "change_type": "modified",
      "detection_method": "line_level_diff"
    }
  ],
  "impacts": {
    "src/libs/ReportUtils.ts:getReportNameInternal": {
      "direct": [
        {
          "name": "getSearchReportName",
          "file_path": "src/libs/ReportUtils.ts",
          "entity_type": "function",
          "relationship_type": "calls",
          "same_file_caller": true
        },
        {
          "name": "processOrder",
          "file_path": "src/services/OrderService.ts",
          "entity_type": "function",
          "relationship_type": "calls"
        }
      ],
      "secondary": [
        {
          "name": "getReportActionsSections",
          "file_path": "src/libs/SearchUIUtils.ts",
          "entity_type": "function",
          "relationship_type": "calls",
          "filter_reason": "actual_usage",
          "priority": 1
        }
      ]
    }
  },
  "dependency_chains": [
    {
      "source": "getReportNameInternal",
      "source_file": "src/libs/ReportUtils.ts",
      "target": "getSearchReportName",
      "target_file": "src/libs/ReportUtils.ts",
      "relationship": "calls",
      "length": 1,
      "risk_level": "medium"
    },
    {
      "source": "getSearchReportName",
      "source_file": "src/libs/ReportUtils.ts",
      "target": "getReportActionsSections",
      "target_file": "src/libs/SearchUIUtils.ts",
      "relationship": "calls",
      "length": 2,
      "risk_level": "medium"
    }
  ],
  "filtering_applied": {
    "intelligent_same_file_filtering": true,
    "description": "Same-file functions are intelligently filtered: keeps direct callers of changed functions (preserves call chains) but removes non-calling same-file functions (reduces noise)"
  },
  "summary": {
    "total_impacted": 715,
    "direct_impacts": 68,
    "secondary_impacts": 722,
    "entity_counts": {
      "function": 669,
      "file": 46
    },
    "risk_counts": {
      "high": 0,
      "medium": 447,
      "low": 268
    }
  }
}
```

### Key Improvements with Intelligent Filtering:

1. **Complete Call Chain Preserved**: 
   - `getReportActionsSections()` → `getSearchReportName()` → `getReportNameInternal()`
   - All three functions are captured in their correct impact levels

2. **Same-File Caller Identified**:
   - `getSearchReportName` marked with `same_file_caller: true`
   - Shows it's an important intermediate function, not noise

3. **Enhanced Metadata**:
   - `filtering_applied` section documents the intelligent filtering approach
   - `same_file_caller` flags help distinguish important same-file dependencies

## Risk Assessment

The system assesses risk based on:

1. **Change Type**
   - `deleted`: High risk (breaking change)
   - `modified`: Medium risk (potential breaking)
   - `added`: Low risk (usually safe)

2. **Relationship Type**
   - `calls`: Higher risk (direct dependency)
   - `imports`: Medium risk (module dependency)
   - `transitive`: Lower risk (indirect)

## Performance Optimization

### Query Optimization
- Use indexed properties (name, file_path)
- Limit result sets early in queries
- Batch similar queries together

### Caching Strategy
- Cache frequently queried entities
- Reuse Neo4j session across queries
- Minimize round trips to database

## Debugging Tips

### Enable Verbose Logging
```python
# See actual Cypher queries
neo4j_client.debug = True

# See filtering decisions
dependency_resolver.verbose = True
```

### Common Issues

1. **Too Many Results**
   - Lower `MAX_SECONDARY_IMPACTS`
   - Increase threshold values
   - Check if test files are included

2. **Missing Dependencies**
   - Verify main KG is complete
   - Check for dynamic imports
   - Ensure file paths match
   - Verify intelligent filtering isn't too aggressive

3. **Broken Call Chains**
   - Check if important same-file callers are being filtered
   - Look for `same_file_caller: true` in direct impacts
   - Verify intermediate functions in call chains

4. **Slow Queries**
   - Check Neo4j indexes
   - Reduce traversal depth
   - Use query profiling

## Future Enhancements

1. **Dynamic Import Detection**: Handle require() and dynamic imports
2. **Type Dependency Tracking**: Follow TypeScript type changes
3. **Test Coverage Integration**: Link impacts to test files
4. **Confidence Scoring**: Rate impact likelihood
5. **Visualization**: Generate dependency graphs