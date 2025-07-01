# Code Graph Documentation

## Overview

The Code Graph feature provides TreeSitter-based parsing and analysis of source code, creating a queryable graph of code elements and their relationships. This enables powerful code navigation, dependency analysis, and architectural insights.

## Architecture

### Components

1. **SQLite Database Layer** (`libs/sqlite/codegraph/`)
   - `codegraph_queries.py`: SQL schema and queries
   - `codegraph_sqlite_client.py`: Database operations and models

2. **Parsing Service** (`services/codegraph_service/`)
   - `treesitter_parser.py`: TreeSitter parsing with regex fallback
   - `graph_builder.py`: Orchestrates parsing and database operations

3. **API Layer** (`controllers/codegraph_controller.py`)
   - REST endpoints for graph operations

### Database Schema

#### Tables

**code_files**
- Tracks source files and their parsing status
- Includes content hash for incremental updates

**code_nodes**
- Represents code elements (functions, classes, variables, imports)
- Stores location, signature, and metadata

**code_relationships**
- Represents relationships between nodes
- Types: calls, imports, inherits, contains, references

### Supported Languages

- TypeScript (.ts)
- TSX (.tsx) 
- JavaScript (.js, .jsx)
- Python (.py)
- Java (.java)
- C/C++ (.c, .cpp, .h, .hpp)

## Usage

### Indexing Code

```python
from services.codegraph_service.graph_builder import CodeGraphBuilder

# Initialize builder
builder = CodeGraphBuilder()

# Index a directory
stats = builder.index_directory("/path/to/code", recursive=True)
print(f"Processed {stats['processed_files']} files")
print(f"Created {stats['total_nodes']} nodes")

# Index a single file  
result = builder.index_file("/path/to/file.ts")

builder.close()
```

### Querying the Graph

```python
# Search for nodes
results = builder.search_nodes("MyClass", node_type="class")

# Get node relationships
relationships = builder.get_node_relationships(node_id)

# Get function call graph
call_graph = builder.get_function_call_graph()

# Get import dependencies
imports = builder.get_import_dependencies()

# Get class hierarchy
hierarchy = builder.get_class_hierarchy()

# Get statistics
stats = builder.get_graph_stats()
```

### API Endpoints

#### Index Operations
- `POST /api/codegraph/index?directory_path=/path&recursive=true`
- `POST /api/codegraph/index-file?file_path=/path/file.ts`

#### Query Operations
- `GET /api/codegraph/stats` - Graph statistics
- `GET /api/codegraph/search?query=term&node_type=function` - Search nodes
- `GET /api/codegraph/node/{id}` - Node details with relationships
- `GET /api/codegraph/nodes/{type}` - All nodes of a type

#### Analysis Operations
- `GET /api/codegraph/call-graph` - Function call relationships
- `GET /api/codegraph/imports` - Import dependencies  
- `GET /api/codegraph/classes` - Class inheritance hierarchy

## Node Types

### Functions
- Regular functions: `function name(params)`
- Arrow functions: `const name = (params) =>`
- Methods: class member functions
- Metadata: parameters, return type, async status

### Classes
- Class declarations with optional inheritance
- Metadata: parent classes, member methods

### Imports
- Named imports: `import { name } from 'module'`
- Default imports: `import name from 'module'`
- Metadata: module path, import type

### Variables
- Variable declarations and assignments
- Constants and let/var declarations

## Relationship Types

### Inheritance (`inherits`)
- Class A extends Class B
- Source: child class, Target: parent class

### Function Calls (`calls`)  
- Function A calls Function B
- Source: caller, Target: callee

### Imports (`imports`)
- File A imports Symbol from Module B
- Source: importing symbol, Target: module/symbol

### Contains (`contains`)
- Class A contains Method B
- Source: container, Target: contained element

## Configuration

### Ignored Patterns
The parser skips common directories and files:
- `node_modules/`, `.git/`, `__pycache__/`
- `dist/`, `build/`, `.vscode/`
- `.min.js`, `.test.`, `.spec.`
- Type definition files (`types.ts`)

### TreeSitter Setup
For full parsing capabilities, install TreeSitter:

```bash
pip install tree-sitter tree-sitter-typescript
```

Without TreeSitter, the system uses regex-based fallback parsing.

## Example Workflow

1. **Initial Indexing**
   ```bash
   curl -X POST "http://localhost:8000/api/codegraph/index?directory_path=/project/src&recursive=true"
   ```

2. **Search for Functions**
   ```bash
   curl "http://localhost:8000/api/codegraph/search?query=process&node_type=function"
   ```

3. **Analyze Dependencies**
   ```bash
   curl "http://localhost:8000/api/codegraph/imports"
   ```

4. **Get Statistics**
   ```bash
   curl "http://localhost:8000/api/codegraph/stats"
   ```

## Performance Considerations

- **Incremental Updates**: Files are re-parsed only when content changes
- **Content Hashing**: SHA256 hashing detects file modifications
- **Batch Processing**: Directory indexing processes files in batches
- **Database Indexing**: Optimized queries with proper database indexes

## Limitations

### Current Implementation
- Regex fallback has limited accuracy without TreeSitter
- Cross-file relationships require symbol resolution
- Limited support for complex language constructs
- No semantic analysis (types, scopes)

### Future Enhancements
- Full TreeSitter integration for all supported languages
- Enhanced relationship detection
- Symbol resolution across files
- Integration with Language Server Protocol (LSP)
- Neo4j backend option for complex graph queries

## Error Handling

The system handles various error conditions:
- **File Access**: Skips unreadable files
- **Parse Errors**: Marks files with error status
- **Database Errors**: Transactional operations with rollback
- **Missing Dependencies**: Graceful fallback to regex parsing

## Monitoring

Track indexing progress and errors:
- File processing statistics
- Parse success/failure rates  
- Node and relationship counts
- Performance metrics

## Integration

### With Blame Detection
Use code graph to enhance blame analysis:
- Find functions modified in PRs
- Analyze call graphs for impact assessment
- Track dependency changes

### With Documentation
Generate documentation from code structure:
- API documentation from function signatures
- Architecture diagrams from relationships
- Dependency graphs for system understanding

### With Testing
Identify test coverage gaps:
- Map tests to source functions
- Find untested code paths
- Analyze test dependencies