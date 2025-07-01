# Code Graph Feature

A TreeSitter-based code analysis system that creates a queryable graph of code elements and their relationships.

## Quick Start

### 1. Install Dependencies (Optional)
For full TreeSitter parsing capabilities:
```bash
pip install tree-sitter tree-sitter-typescript
```

*Note: The system works with regex-based fallback parsing if TreeSitter is not available.*

### 2. Index Your Code
```python
from services.codegraph_service.graph_builder import CodeGraphBuilder

builder = CodeGraphBuilder()
stats = builder.index_directory("/path/to/your/code")
print(f"Indexed {stats['total_nodes']} code elements")
builder.close()
```

### 3. Query the Graph
```python
# Search for functions
functions = builder.search_nodes("process", node_type="function")

# Get class hierarchy
hierarchy = builder.get_class_hierarchy()

# Analyze imports
imports = builder.get_import_dependencies()
```

## API Endpoints

Start the server and use these endpoints:

### Index Code
```bash
# Index a directory
curl -X POST "http://localhost:8000/api/codegraph/index?directory_path=/src&recursive=true"

# Index a single file  
curl -X POST "http://localhost:8000/api/codegraph/index-file?file_path=/src/utils.ts"
```

### Query Graph
```bash
# Get statistics
curl "http://localhost:8000/api/codegraph/stats"

# Search for nodes
curl "http://localhost:8000/api/codegraph/search?query=MyClass&node_type=class"

# Get node details
curl "http://localhost:8000/api/codegraph/node/123"

# Get function calls
curl "http://localhost:8000/api/codegraph/call-graph"

# Get imports
curl "http://localhost:8000/api/codegraph/imports"

# Get class hierarchy
curl "http://localhost:8000/api/codegraph/classes"
```

## Example Analysis

Use the provided example script to analyze any codebase:

```bash
cd examples
python codegraph_example.py /path/to/your/project
```

This will:
- Index all source files
- Generate statistics and insights
- Identify complex classes and files
- Analyze import patterns
- Export results to JSON

## Supported Languages

- **TypeScript** (.ts, .tsx) - Functions, classes, imports, inheritance
- **JavaScript** (.js, .jsx) - Functions, classes, imports, inheritance  
- **Python** (.py) - Functions, classes, imports, inheritance
- **Java** (.java) - Classes, methods, imports
- **C/C++** (.c, .cpp, .h, .hpp) - Functions, structs, includes

## What Gets Extracted

### Code Elements (Nodes)
- **Functions**: Regular functions, arrow functions, methods
- **Classes**: Class declarations with inheritance
- **Imports**: Named and default imports
- **Variables**: Constants and variable declarations

### Relationships  
- **Inheritance**: Class A extends Class B
- **Function Calls**: Function A calls Function B  
- **Imports**: File imports symbol from module
- **Contains**: Class contains method

## Use Cases

### 1. Code Navigation
Find all usages of a function or class across your codebase:
```python
results = builder.search_nodes("UserService")
for result in results:
    print(f"{result['type']} {result['name']} in {result['file_path']}")
```

### 2. Dependency Analysis
Understand module dependencies:
```python
imports = builder.get_import_dependencies()
for imp in imports:
    print(f"{imp['importing_file']} depends on {imp['imported_name']}")
```

### 3. Architecture Analysis
Find the most complex classes:
```python
classes = builder.search_nodes("", "class")
for cls in classes:
    rels = builder.get_node_relationships(cls['id'])
    complexity = len(rels['incoming']) + len(rels['outgoing'])
    print(f"{cls['name']}: {complexity} relationships")
```

### 4. Impact Analysis
Before refactoring, see what might be affected:
```python
# Find all classes that inherit from BaseService
hierarchy = builder.get_class_hierarchy()
base_service_children = [
    h for h in hierarchy 
    if h['parent_class'] == 'BaseService'
]
```

## Performance

- **Incremental**: Only re-parses files when content changes
- **Efficient**: Uses content hashing to detect modifications
- **Scalable**: SQLite backend with proper indexing
- **Fast**: Regex fallback for quick parsing without TreeSitter

## Limitations

### Current
- Cross-file function calls require TreeSitter for accuracy
- Limited semantic analysis (no type checking)
- No scope analysis within functions

### Planned Improvements
- Full TreeSitter integration
- Symbol resolution across files
- Neo4j backend option for complex queries
- Language Server Protocol integration

## Database Schema

The system uses SQLite with three main tables:

- **code_files**: Tracks files and parsing status
- **code_nodes**: Stores code elements (functions, classes, etc.)
- **code_relationships**: Stores relationships between elements

See [docs/codegraph.md](docs/codegraph.md) for complete schema details.

## Contributing

To extend language support:

1. Add language detection in `treesitter_parser.py`
2. Implement regex patterns for the language
3. Add TreeSitter grammar (optional)
4. Update file extension mapping

## Examples

See the `examples/` directory for:
- Basic usage examples
- Complete codebase analysis
- API integration examples
- Custom analysis scripts