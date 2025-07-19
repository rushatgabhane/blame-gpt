# Review Bot

A knowledge graph-based code review system that analyzes pull requests and provides intelligent feedback by understanding code relationships and dependencies.

## Structure

```
services/review_bot/
├── config.py                  # Configuration settings
├── core/                      # Core KG building components
│   ├── entity_extraction.py   # Extract entities from code using tree-sitter
│   ├── relationship_builder.py # Build relationships between entities
│   └── knowledge_graph_builder.py # Orchestrate main KG construction
├── analysis/                  # PR analysis components
│   ├── pr_diff_analyzer.py    # Analyze PR diffs and build mini KG
│   └── dependency_resolver.py # Query main KG for impacted entities (TODO)
├── context/                   # Context building components
│   └── context_builder.py     # Smart code fetching (TODO)
├── generation/                # Review generation
│   └── review_generator.py    # LLM integration (TODO)
├── examples/                  # Example scripts
│   ├── example_usage.py       # Demo main KG building
│   ├── example_pr_mini_kg.py  # Demo PR analysis
│   └── test_pr_analyzer.py    # Test PR analyzer
└── outputs/                   # Generated files
    └── *.json                 # Analysis outputs
```

## Workflow

1. **Main KG**: Build complete knowledge graph from repository HEAD
2. **Mini KG**: Analyze PR changes to create focused change graph  
3. **Dependency Analysis**: Query main KG to find impacted entities
4. **Context Building**: Fetch relevant code snippets
5. **Review Generation**: Send context to LLM for intelligent review

## Usage

```python
# Build main knowledge graph
from services.review_bot import KnowledgeGraphBuilder
builder = KnowledgeGraphBuilder()
builder.build_knowledge_graph()

# Analyze a PR
from services.review_bot import PRDiffAnalyzer
analyzer = PRDiffAnalyzer()
result = analyzer.analyze_pr(12345)
```

## Examples

```bash
# Demo main KG building
python examples/example_usage.py

# Demo PR analysis
python examples/example_pr_mini_kg.py 65748
```