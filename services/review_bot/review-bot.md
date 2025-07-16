# Review Bot Knowledge Graph Implementation

## Overview

This module implements a comprehensive knowledge graph builder for JavaScript/TypeScript codebases using the **latest commit state** instead of baseline commits. The implementation follows the same flow as the original Jupyter notebook but is modularized into reusable Python components that integrate with the existing BlameGPT codebase structure.

## What Has Been Implemented

### 1. Entity Extraction (`entity_extraction.py`)

**Purpose**: Parses JavaScript/TypeScript files using tree-sitter to extract code entities.

**Features**:
- **Tree-sitter Integration**: Uses `tree-sitter-javascript` and `tree-sitter-typescript` for accurate AST parsing
- **Multi-language Support**: Handles both JavaScript and TypeScript files
- **Comprehensive Entity Detection**:
  - Functions (declarations, arrow functions, method definitions, function expressions)
  - Classes (class declarations)
  - Variables (const, let, var declarations)
  - Imports (named imports, default imports, external modules)
  - Exports (named exports, default exports)
  - Function calls (direct calls, method calls, constructor calls)

**Key Methods**:
- `analyze_file(file_path)`: Main entry point that returns all extracted entities
- Individual extractors for each entity type with precise AST node matching

### 2. Relationship Builder (`relationship_builder.py`)

**Purpose**: Creates relationships and dependencies between extracted entities.

**Relationship Types**:
- **File Relationships**: Import/export connections between files
- **Function Call Relationships**: Within-file function invocations
- **Cross-file Dependencies**: Function calls across file boundaries using import aliases
- **Entity Relationships**: Class-to-method relationships, function containment
- **Variable Usage**: Variable declaration and usage tracking

**Key Features**:
- **Import Path Resolution**: Resolves relative and absolute import paths to actual files
- **Alias Mapping**: Tracks imported names and their aliases for cross-file analysis
- **Context-aware Analysis**: Understands scope and containment relationships

### 3. Neo4j Client (`libs/neo4j_client.py`)

**Purpose**: Manages all Neo4j database operations with optimized bulk loading.

**Capabilities**:
- **Connection Management**: Handles Neo4j driver lifecycle
- **Schema Initialization**: Creates constraints and indexes for optimal performance
- **Bulk Data Loading**: Efficient batch operations for large codebases
- **Node Types Created**:
  - `File`: Repository files with metadata (size, entity counts)
  - `Function`: Function declarations with line numbers and types
  - `Class`: Class declarations
  - `Variable`: Variable declarations
  - `ExternalModule`: External dependencies
  - `FunctionCall`: Function call instances

**Relationship Types Created**:
- `CONTAINS`: Files contain entities
- `IMPORTS`: Internal file dependencies
- `IMPORTS_EXTERNAL`: External module dependencies
- `CALLS`: Function call relationships
- `INVOKES`: Resolved function invocations

### 4. Knowledge Graph Builder (`knowledge_graph_builder.py`)

**Purpose**: Orchestrates the entire knowledge graph construction process.

**Process Flow** (following notebook implementation):
1. **Repository State Analysis**: Gets current commit info (latest state, not baseline)
2. **File Discovery**: Finds all JavaScript/TypeScript files in `src/` directory
3. **Entity Extraction**: Processes each file to extract code entities
4. **Relationship Building**: Creates connections between entities
5. **Neo4j Loading**: Bulk loads all data into the graph database

**Key Differences from Notebook**:
- ✅ **Uses Latest Commit**: No baseline selection, uses current repository state
- ✅ **Modular Architecture**: Separated concerns into reusable components
- ✅ **Error Handling**: Comprehensive error handling and progress reporting
- ✅ **Statistics Tracking**: Detailed metrics throughout the process

### 5. Configuration (`config.py`)

**Purpose**: Centralized configuration management.

**Settings**:
- Neo4j connection parameters
- File discovery patterns and exclusions
- Processing batch sizes
- Docker container settings for local development

### 6. Integration Files

- `__init__.py`: Module initialization and exports
- `example_usage.py`: Demonstration script showing how to use the system

## Architecture Decisions

### Why This Approach?

1. **Latest Commit Focus**: Instead of complex baseline selection, we use the current repository state which is simpler and more relevant for review bot analysis

2. **Modular Design**: Each component has a single responsibility:
   - Entity extraction is separate from relationship building
   - Database operations are isolated in the Neo4j client
   - Configuration is centralized

3. **BlameGPT Integration**: Follows the existing codebase structure:
   - Services in `services/` directory
   - Shared libraries in `libs/`
   - Consistent with existing patterns

4. **Performance Optimized**: 
   - Bulk database operations
   - Efficient tree-sitter parsing
   - Batch processing with progress tracking

## Data Model

### Nodes
```
File {path, name, extension, size_bytes, entity_counts...}
Function {name, file_path, start_line, end_line, ast_type}
Class {name, file_path, start_line, end_line, ast_type}
Variable {name, file_path, start_line, end_line, type}
ExternalModule {name}
FunctionCall {target, line, call_type}
```

### Relationships
```
(File)-[:CONTAINS]->(Entity)
(File)-[:IMPORTS]->(File)
(File)-[:IMPORTS_EXTERNAL]->(ExternalModule)
(File)-[:CALLS]->(FunctionCall)
(Function)-[:INVOKES]->(Function)
```

## Usage

### Basic Usage (GitHub Integration)
```python
from services.review_bot import KnowledgeGraphBuilder

# Builds KG for the configured repository (Expensify/App)
builder = KnowledgeGraphBuilder()
result = builder.build_knowledge_graph()
```

### With Custom Neo4j Settings
```python
builder = KnowledgeGraphBuilder(
    neo4j_uri="bolt://localhost:7687",
    neo4j_user="neo4j",
    neo4j_password="your_password",
    use_temp_dir=True  # Use temporary directory for cloning
)
```

### Via API Endpoints
```bash
# Start knowledge graph build
curl -X POST "http://localhost:8000/api/review-bot/build" \
  -H "Content-Type: application/json" \
  -d '{"neo4j_uri": "bolt://localhost:7687"}'

# Check build status  
curl "http://localhost:8000/api/review-bot/build/{build_id}/status"
```

## Prerequisites

### Required Dependencies (added to requirements.txt)
- `tree-sitter==0.24.0`
- `tree-sitter-javascript==0.23.4`
- `tree-sitter-typescript==0.23.2`
- `neo4j==5.28.0`
- `pydriller==2.8`

### Neo4j Setup
```bash
# Start Neo4j with Docker
docker run -d \
  --name neo4j-kg \
  --publish=7474:7474 \
  --publish=7687:7687 \
  --env NEO4J_AUTH=neo4j/password \
  neo4j:5.20
```

## Example Queries

After building the knowledge graph, you can query it:

```cypher
// Files with most function calls
MATCH (f:File)-[:CALLS]->()
RETURN f.name, count(*) as call_count
ORDER BY call_count DESC

// Cross-file dependencies
MATCH (f1:File)-[:IMPORTS]->(f2:File)
RETURN f1.name, f2.name

// Function complexity analysis
MATCH (func:Function)
RETURN func.name, func.end_line - func.start_line as lines_of_code
ORDER BY lines_of_code DESC
```

## Benefits for Review Bot

1. **Code Understanding**: Complete visibility into codebase structure and relationships
2. **Dependency Analysis**: Track how changes propagate through the codebase
3. **Complexity Metrics**: Identify complex functions and files for focused review
4. **Pattern Detection**: Find similar code patterns and architectural inconsistencies
5. **Impact Analysis**: Understand the scope of changes and potential affected areas

## Next Steps

This knowledge graph foundation enables:
- **Performance Review Bot**: Analyze performance improvement patterns
- **Deploy Blocker Prevention**: Identify risky code patterns
- **Code Quality Metrics**: Measure complexity and maintainability
- **Automated Refactoring Suggestions**: Based on architectural patterns
- **Test Coverage Analysis**: Understand testing gaps in critical paths

The implementation is ready for integration with the existing BlameGPT infrastructure and can be extended with additional analysis capabilities as needed.