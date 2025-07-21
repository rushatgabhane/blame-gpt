# Main Knowledge Graph Building Process

## Overview

The main knowledge graph (KG) building process creates a comprehensive semantic representation of the entire codebase. This KG serves as the foundation for analyzing pull request impacts and understanding code dependencies.

## Process Flow

```
1. Repository Cloning
        ↓
2. File Discovery
        ↓
3. Entity Extraction (per file)
        ↓
4. Relationship Building
        ↓
5. Neo4j Loading
        ↓
6. Post-processing (cross-file relationships)
```

## Detailed Steps

### 1. Repository Cloning

The `KnowledgeGraphBuilder.clone_repository()` method:
- Clones from: `https://github.com/{REPO_OWNER}/{REPO_NAME}.git`
- Uses shallow clone (`--depth 1`) for efficiency
- Supports two modes:
  - **Temporary directory**: Cleans up after processing
  - **Local directory**: Keeps repository for faster subsequent runs (default)

```python
# Configuration from libs/constants.py
REPO_OWNER = "Expensify"
REPO_NAME = "App"
```

### 2. File Discovery

The `discover_files()` method finds all relevant source files:

**Supported file types:**
- `.js` - JavaScript files
- `.jsx` - React JavaScript files  
- `.ts` - TypeScript files
- `.tsx` - React TypeScript files

**Excluded patterns:**
- `test`, `spec`, `__tests__` - Test files
- `node_modules` - Dependencies
- `.git` - Version control
- `dist`, `build` - Build artifacts

**Discovery scope:** Only files within the `src/` directory

### 3. Entity Extraction

For each discovered file, the `EntityExtractor` parses and extracts:

#### Functions
```typescript
{
  name: "getCurrentUserAvatar",
  file_path: "src/libs/ReportUtils.ts",
  start_line: 1124,
  end_line: 1126,
  ast_type: "FunctionDeclaration",
  signature: "function getCurrentUserAvatar(): string | undefined",
  parameters: [],
  is_async: false,
  is_exported: true
}
```

#### Classes
```typescript
{
  name: "ReportManager",
  file_path: "src/libs/ReportManager.ts",
  start_line: 45,
  end_line: 234,
  ast_type: "ClassDeclaration",
  methods: ["initialize", "getReport", "updateReport"],
  is_exported: true
}
```

#### Variables/Constants
```typescript
{
  name: "MAX_REPORT_SIZE",
  file_path: "src/constants/limits.ts",
  start_line: 12,
  end_line: 12,
  ast_type: "VariableDeclaration",
  kind: "const",
  is_exported: true
}
```

#### Imports
```typescript
{
  source: "react",
  imported_names: ["useState", "useEffect"],
  import_line: 1,
  import_stmt: "import { useState, useEffect } from 'react'",
  alias_map: {}
}
```

#### Function Calls
```typescript
{
  target: "calculateTotal",
  line: 156,
  call_type: "direct_call"
}
```

### 4. Relationship Building

The `RelationshipBuilder` creates connections between entities:

#### File-to-File Relationships
- **IMPORTS**: When one file imports another
- **IMPORTS_EXTERNAL**: When importing external modules

#### Entity Containment
- **CONTAINS**: Files contain functions, classes, and variables

#### Function Invocations
- **INVOKES**: Function-to-function call relationships
- Handles both same-file and cross-file calls

### 5. Neo4j Schema

The knowledge graph uses this schema:

#### Node Types
1. **File**
   - Properties: path, name, relative_path, extension, size_bytes
   - Metrics: function_count, class_count, variable_count

2. **Function**
   - Properties: name, file_path, start_line, end_line, signature
   - Metadata: is_async, is_exported, parameters

3. **Class**
   - Properties: name, file_path, start_line, end_line
   - Metadata: methods, is_exported

4. **Variable**
   - Properties: name, file_path, start_line, end_line
   - Metadata: kind (const/let/var), is_exported

5. **ExternalModule**
   - Properties: name (e.g., "react", "lodash")

6. **FunctionCall**
   - Properties: file_path, line, target, call_type

#### Relationship Types
1. **CONTAINS**: File → Function/Class/Variable
2. **IMPORTS**: File → File
3. **IMPORTS_EXTERNAL**: File → ExternalModule
4. **CALLS**: File → FunctionCall
5. **INVOKES**: Function → Function

### 6. Loading Process

The loading follows this sequence:

1. **Initialize Schema**: Create constraints and indexes
2. **Load Files**: Create File nodes with metadata
3. **Load Entities**: Create Function, Class, Variable nodes
4. **Load CONTAINS**: Connect files to their entities
5. **Load Imports**: Create import relationships
6. **Load Function Calls**: Create FunctionCall nodes
7. **Resolve Same-File Calls**: Create INVOKES for internal calls
8. **Resolve Cross-File Calls**: Create INVOKES for external calls

### 7. Cypher Query Examples

**Find all functions in a file:**
```cypher
MATCH (f:File {name: "ReportUtils.ts"})-[:CONTAINS]->(fn:Function)
RETURN fn.name, fn.start_line, fn.signature
```

**Find who calls a specific function:**
```cypher
MATCH (caller:Function)-[:INVOKES]->(target:Function {name: "getCurrentUserAvatar"})
RETURN caller.name, caller.file_path
```

**Find import dependencies:**
```cypher
MATCH (f1:File)-[:IMPORTS]->(f2:File)
WHERE f2.name = "ReportUtils.ts"
RETURN f1.name as importer
```

## Performance Considerations

### Processing Statistics (typical for Expensify/App)
- Files discovered: ~2,000-3,000
- Total entities: ~50,000-100,000
- Processing time: 2-5 minutes
- Neo4j load time: 1-2 minutes

### Optimization Strategies
1. **Shallow clone**: Only fetches latest commit
2. **Batch loading**: Processes files in batches
3. **Parallel entity extraction**: Could be implemented
4. **Reuse local repository**: Avoids repeated cloning

## Error Handling

The system handles various failure scenarios:
- **Parse errors**: Logged but don't stop processing
- **Missing files**: Skipped with warning
- **Neo4j connection**: Fails fast with clear error
- **Memory issues**: Batch processing prevents OOM

## Usage

### Basic Usage
```python
# Run from examples/example_usage.py
python services/review_bot/examples/example_usage.py
```

### Programmatic Usage
```python
from services.review_bot.core import KnowledgeGraphBuilder
from services.review_bot.config import ReviewBotConfig

# Get Neo4j config
neo4j_config = ReviewBotConfig.get_neo4j_config()

# Initialize builder
builder = KnowledgeGraphBuilder(
    neo4j_uri=neo4j_config["uri"],
    neo4j_user=neo4j_config["user"],
    neo4j_password=neo4j_config["password"],
    use_temp_dir=False  # Keep repo locally
)

# Build the knowledge graph
result = builder.build_knowledge_graph()

if result['status'] == 'success':
    print(f"Entities: {result['total_entities']}")
    print(f"Relationships: {result['total_relationships']}")
```

## Verification

After building, verify the KG in Neo4j Browser:

1. Open http://localhost:7474
2. Run: `MATCH (n) RETURN n LIMIT 100`
3. Explore the graph visually

Common verification queries:
```cypher
// Count nodes by type
MATCH (n) 
RETURN labels(n)[0] as type, count(n) as count
ORDER BY count DESC

// Find most called functions
MATCH (fn:Function)<-[:INVOKES]-()
RETURN fn.name, fn.file_path, count(*) as call_count
ORDER BY call_count DESC
LIMIT 10
```