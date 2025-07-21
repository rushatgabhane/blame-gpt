# Review Bot Architecture Overview

## Purpose

The Review Bot is an intelligent code review system that analyzes pull requests (PRs) to identify the potential impact of code changes across a codebase. It builds a comprehensive knowledge graph of the entire codebase and uses it to trace dependencies and understand how changes propagate through the system.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Review Bot                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Main KG Builder          2. PR Analysis Pipeline        │
│  ┌─────────────────┐         ┌─────────────────────┐       │
│  │ Clone Repository│         │ Fetch PR Diff       │       │
│  │       ↓         │         │       ↓             │       │
│  │ Entity Extract  │         │ Enhanced Diff       │       │
│  │       ↓         │         │ Analysis            │       │
│  │ Relationship    │         │       ↓             │       │
│  │ Builder         │         │ Mini KG Generation  │       │
│  │       ↓         │         │       ↓             │       │
│  │ Load to Neo4j   │         │ Dependency Analysis │       │
│  └─────────────────┘         └─────────────────────┘       │
│                                                             │
│  ┌───────────────────────────────────────────────────┐     │
│  │                   Neo4j Database                   │     │
│  │  - Files, Functions, Classes, Variables           │     │
│  │  - CONTAINS, IMPORTS, INVOKES relationships       │     │
│  └───────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Knowledge Graph Builder (`core/knowledge_graph_builder.py`)
- **Purpose**: Builds the complete knowledge graph of the codebase
- **Process**:
  - Clones the repository from GitHub
  - Discovers all JavaScript/TypeScript files
  - Extracts entities (functions, classes, variables)
  - Builds relationships (imports, function calls, containment)
  - Loads everything into Neo4j database

### 2. Entity Extraction (`core/entity_extraction.py`)
- **Purpose**: Parses source code files to extract semantic entities
- **Extracts**:
  - Functions (with signatures, line numbers)
  - Classes (with methods, properties)
  - Variables (constants, exports)
  - Import statements
  - Function calls

### 3. Relationship Builder (`core/relationship_builder.py`)
- **Purpose**: Identifies relationships between entities
- **Builds**:
  - File-to-file imports
  - Function invocations (who calls whom)
  - Containment (which file contains which functions)
  - Cross-file function calls

### 4. PR Diff Analyzer (`analysis/pr_diff_analyzer.py`)
- **Purpose**: Analyzes pull request changes
- **Features**:
  - Fetches PR diffs from GitHub
  - Identifies added/modified/deleted files
  - Compares entities before and after changes
  - Builds a mini KG of changes

### 5. Enhanced Diff Analyzer (`analysis/enhanced_diff_analyzer.py`)
- **Purpose**: Provides line-level precision for change detection
- **Innovation**: 
  - Parses actual diff hunks to find exact changed lines
  - Maps changed lines to containing functions
  - Reduces false positives in impact analysis

### 6. Dependency Resolver (`analysis/dependency_resolver.py`)
- **Purpose**: Identifies all code impacted by PR changes
- **Features**:
  - Queries main KG to find dependencies
  - **Intelligent Same-File Filtering**: Preserves call chains while reducing noise
  - Categorizes impacts (direct, secondary, tertiary)
  - Three smart filtering strategies:
    1. **Actual Usage**: Functions that directly call changed code
    2. **High Centrality**: Functions called by many others
    3. **Orchestrators**: Functions that coordinate many calls

## Data Flow

### Phase 1: Main KG Construction
1. **Repository Cloning**: Fetches latest code from GitHub
2. **File Discovery**: Finds all JS/TS files in src/
3. **Entity Extraction**: Parses each file for semantic entities
4. **Relationship Building**: Connects entities based on imports/calls
5. **Neo4j Loading**: Stores complete KG in graph database

### Phase 2: PR Analysis
1. **PR Diff Fetching**: Gets file changes from GitHub API
2. **Enhanced Diff Analysis**: 
   - Parses diff patches for line-level changes
   - Maps changed lines to specific functions
3. **Mini KG Generation**: Creates focused KG of just the changes
4. **Dependency Analysis**:
   - Queries main KG for impacted entities
   - Applies smart filtering for relevance
   - Builds dependency chains

## Key Innovations

### 1. Line-Level Change Detection
- Traditional approaches mark entire files as changed
- Enhanced analyzer pinpoints exact functions with changes
- Dramatically reduces false positives in impact analysis

### 2. Smart Filtering
- Problem: File imports can create massive dependency graphs
- Solution: Three-pronged filtering approach
  - Actual usage detection (most precise)
  - Centrality analysis (important functions)
  - Orchestrator detection (coordination functions)

### 3. Multi-Level Impact Analysis
- **Direct Impact**: Functions that directly call changed code
- **Secondary Impact**: Functions that call the direct impacts
- **Tertiary Impact**: Further propagation (usually filtered)

## Configuration

The system is configured via `config.py`:
- Neo4j connection settings
- File discovery patterns
- Smart filtering thresholds
- Processing batch sizes

## Usage Example

```python
# Build main knowledge graph
builder = KnowledgeGraphBuilder(
    neo4j_uri="bolt://localhost:7687",
    neo4j_user="neo4j",
    neo4j_password="password"
)
result = builder.build_knowledge_graph()

# Analyze a PR
analyzer = EnhancedDiffAnalyzer()
pr_analysis = analyzer.analyze_pr_with_line_diffs(65748)

# Run dependency analysis
resolver = DependencyResolver(neo4j_client)
dependencies = resolver.analyze_dependencies(pr_analysis["mini_kg"])
```

## Output Structure

The system produces a comprehensive JSON output containing:
- PR summary (files changed, lines added/removed)
- Enhanced function changes (with line-level precision)
- Mini KG of the changes
- Dependency analysis results
- Impact chains and risk assessments