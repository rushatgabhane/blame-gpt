# Semantic Metadata Search & Enrichment System

## Overview

This document outlines the implementation of a comprehensive metadata enrichment system that enhances our knowledge graph-based code review bot with semantic search capabilities and intelligent context filtering. The system addresses the critical challenge of reducing 9,591+ dependency impacts to a manageable ~30 entities for LLM review.

## Current Challenge

Our dependency resolver successfully identifies all impacted entities when code changes occur, but produces overwhelming results:

### Real Example: PR 65748 Analysis
- **Input**: PR with 2 modified files (only 1 line changed in `ReportUtils.ts`)
- **Direct Impacts (23 entities)**: Files that directly import the changed file
  - `ReportPreviewActionUtils.ts` imports `ReportUtils.ts`
  - `QuickActionUtils.ts` imports `ReportUtils.ts`
  - 21 other files that import `ReportUtils.ts`
- **Secondary Impacts (9,568 entities)**: All functions within the directly impacted files
  - All 400+ functions in `ReportPreviewActionUtils.ts`
  - All 200+ functions in `QuickActionUtils.ts`
  - All functions in the other 21 importing files
- **Total**: 23 + 9,568 = 9,591 entities

### The Core Problem
**Reality**: A 1-line change in a utility file likely affects only 2-3 functions
**Current Output**: 9,591 potentially impacted entities (99.9% false positives)
**Review Challenge**: No human can meaningfully review 9,591 entities

### Why This Happens
The dependency resolver uses a conservative approach:
1. **Direct Impact Detection**: Find files that import the changed file ✓ (accurate)
2. **Secondary Impact Explosion**: Flag ALL functions in importing files ✗ (too broad)
3. **No Filtering**: Every function marked as "potentially affected" ✗ (unusable)

This is where **semantic metadata search** becomes critical - we need intelligent filtering to identify which of these 9,568 secondary impacts actually matter.

## Solution Architecture

### High-Level Flow

```
┌─────────────────┐         ┌─────────────────┐
│   Main KG       │ ◄────── │ Metadata Store  │
│   (Neo4j)       │         │                 │
│                 │         │ • Embeddings    │
│ Syntactic Data  │ ────►   │ • Criticality   │
│ - Files         │ enrich  │ • Domain        │
│ - Functions     │         │ • Complexity    │
│ - Dependencies  │         │ • Usage Stats   │
└─────────────────┘         └─────────────────┘
         │                           │
         └───────────┬───────────────┘
                     ▼
         ┌─────────────────┐
         │  Smart Filter   │
         │  & Semantic     │
         │  Search Engine  │
         └────────┬────────┘
                  ▼
         ┌─────────────────┐
         │ Context Builder │ ──► ~30 relevant entities
         │  (for LLM)      │     with rich context
         └─────────────────┘
```

## Metadata Components

### 1. Static Code Analysis Metadata

Generated through AST analysis and code metrics:

```json
{
  "complexity_metrics": {
    "cyclomatic_complexity": 12,
    "cognitive_complexity": 8,
    "lines_of_code": 45,
    "parameter_count": 3,
    "return_type_complexity": "medium",
    "nesting_depth": 3
  },
  "code_quality": {
    "has_error_handling": true,
    "has_tests": true,
    "test_coverage": 0.85,
    "has_documentation": true,
    "follows_conventions": true
  }
}
```

### 2. Semantic Analysis Metadata

Generated using LLM embeddings and classification:

```json
{
  "semantic_embeddings": {
    "code_embedding": [0.1, 0.3, 0.8, ...],  // 1536-dim vector
    "description_embedding": [0.2, 0.4, 0.7, ...],
    "signature_embedding": [0.3, 0.5, 0.6, ...]
  },
  "semantic_classification": {
    "business_domain": "financial_processing",
    "functional_category": "calculation",
    "semantic_tags": ["expense", "reimbursement", "validation"],
    "intent": "calculate_total_expenses_for_approval"
  }
}
```

### 3. Usage & Impact Analysis Metadata

Generated from knowledge graph queries:

```json
{
  "usage_patterns": {
    "direct_callers": 23,
    "total_usages": 87,
    "calling_modules": ["ExpenseModule", "ReportModule"],
    "dependency_depth": 3,
    "is_public_api": true,
    "is_critical_path": true
  },
  "impact_analysis": {
    "criticality_score": 9.2,  // 0-10 scale
    "blast_radius": "high",
    "affects_external_api": true,
    "affects_security": false,
    "affects_data_integrity": true
  }
}
```

### 4. Historical & Team Metadata

Generated from git history and codebase patterns:

```json
{
  "historical_data": {
    "change_frequency": "high",  // high/medium/low
    "last_modified": "2024-01-15",
    "bug_fix_count": 3,
    "enhancement_count": 12,
    "breaking_changes": 1
  },
  "ownership": {
    "team": "platform",
    "primary_author": "john.doe",
    "expertise_required": "senior",
    "review_sensitivity": "high"
  }
}
```

## Implementation Architecture

### Component Structure

```
services/review_bot/metadata/
├── __init__.py
├── generators/
│   ├── __init__.py
│   ├── static_analyzer.py      # AST-based analysis
│   ├── semantic_analyzer.py    # LLM-based embeddings
│   ├── usage_analyzer.py       # KG query analysis
│   └── historical_analyzer.py  # Git history analysis
├── storage/
│   ├── __init__.py
│   ├── metadata_store.py       # Storage interface
│   ├── json_store.py          # JSON implementation
│   └── vector_store.py        # Vector DB implementation
├── search/
│   ├── __init__.py
│   ├── semantic_search.py     # Embedding-based search
│   └── hybrid_search.py       # Combined search strategies
└── enrichment/
    ├── __init__.py
    ├── metadata_enricher.py   # Main enrichment logic
    └── context_builder.py     # Smart context creation
```

### Key Classes

#### MetadataGenerator

```python
class MetadataGenerator:
    """Orchestrates all metadata generation strategies."""
    
    def generate_metadata(self, entity):
        return {
            "static": self.static_analyzer.analyze(entity),
            "semantic": self.semantic_analyzer.analyze(entity),
            "usage": self.usage_analyzer.analyze(entity),
            "historical": self.historical_analyzer.analyze(entity)
        }
```

#### SemanticSearchEngine

```python
class SemanticSearchEngine:
    """Provides semantic search capabilities over metadata."""
    
    def find_similar(self, query_entity, threshold=0.8):
        """Find semantically similar entities."""
        
    def search_by_impact(self, min_criticality=7):
        """Search by business impact criteria."""
        
    def group_by_domain(self, entities):
        """Group entities by business domain."""
```

#### SmartContextBuilder

```python
class SmartContextBuilder:
    """Builds optimized context for LLM consumption."""
    
    def build_context(self, dependency_results, max_entities=30):
        """
        Reduces 9,591 entities to ~30 most relevant ones.
        
        Input: dependency_results = {
            "direct_impacts": 23,      # Files importing changed code
            "secondary_impacts": 9568  # ALL functions in importing files
        }
        
        Output: ~30 entities filtered by:
        - Actual usage of changed code
        - Semantic similarity and business domain
        - Criticality score and impact level
        """
```

## Metadata Generation Pipeline

### Phase 1: Initial Analysis (One-time)

1. **Scan entire codebase** through Main KG
2. **Generate static metrics** for all functions/files
3. **Create embeddings** for semantic search
4. **Analyze usage patterns** from dependencies
5. **Store in metadata store**

### Phase 2: Incremental Updates

1. **Monitor code changes** via git hooks
2. **Update affected metadata** only
3. **Refresh embeddings** for modified functions
4. **Recalculate criticality** based on new usage

### Phase 3: Runtime Enrichment

1. **Receive dependency analysis** results (23 direct + 9,568 secondary impacts)
2. **Enrich with metadata** from store (add semantic/usage/criticality data)
3. **Apply smart filtering** based on criteria:
   - **Actual Usage**: Which functions actually call the changed code?
   - **Semantic Similarity**: Which functions handle similar business logic?
   - **Criticality Score**: Which functions are in critical paths?
   - **Domain Grouping**: Which functions belong to the same business domain?
4. **Build optimized context** for LLM (reduce 9,591 → ~30 entities)

## Semantic Search Capabilities

### 1. Similarity Search

Find functions similar to a changed function:
```python
# "calculateTotal changed, find similar calculation functions"
similar = semantic_search.find_similar("calculateTotal", top_k=10)
```

### 2. Domain-Based Search

Find all critical financial functions:
```python
# "Show me high-criticality financial processing functions"
results = semantic_search.search_by_domain(
    domain="financial_processing",
    min_criticality=8
)
```

### 3. Impact-Based Search

Find functions by impact characteristics:
```python
# "Find functions that affect external APIs"
results = semantic_search.search_by_impact(
    affects_external_api=True,
    min_criticality=7
)
```

### 4. Hybrid Search

Combine multiple search strategies:
```python
# "Find similar financial functions with high usage"
results = hybrid_search.search(
    semantic_similarity=0.8,
    domain="financial",
    min_usage_frequency=50
)
```

## Benefits & Use Cases

### 1. Intelligent PR Review

**Before**: Review 9,591 potentially impacted entities
- 23 direct impacts (files importing changed code)
- 9,568 secondary impacts (ALL functions in importing files)
- 99.9% false positive rate

**After**: Review ~30 highly relevant entities with rich context
- 5-10 functions that actually use the changed code
- 10-15 semantically similar functions (same business domain)
- 5-10 critical path functions (high impact, external APIs)
- Rich metadata explaining WHY each is relevant

### 2. Risk Assessment

- Automatically identify high-risk changes
- Prioritize review efforts on critical code
- Detect changes to security-sensitive functions

### 3. Smart Context Building

- Group related changes by business domain
- Provide semantic explanations to LLM
- Include only relevant code snippets

### 4. Code Discovery

- Find similar implementations across codebase
- Identify potential refactoring opportunities
- Detect duplicate functionality

## Implementation Roadmap

### Phase 1: Foundation (Week 1-2)
- [ ] Set up metadata storage infrastructure
- [ ] Implement static code analyzer
- [ ] Create basic metadata schema

### Phase 2: Semantic Layer (Week 3-4)
- [ ] Integrate OpenAI embeddings
- [ ] Implement semantic classifier
- [ ] Build vector storage for embeddings

### Phase 3: Search Engine (Week 5-6)
- [ ] Implement semantic search
- [ ] Create hybrid search strategies
- [ ] Build search API

### Phase 4: Integration (Week 7-8)
- [ ] Integrate with dependency resolver
- [ ] Implement smart context builder
- [ ] Create enrichment pipeline

### Phase 5: Optimization (Week 9-10)
- [ ] Performance tuning
- [ ] Caching strategies
- [ ] Incremental update system

## Configuration

### Environment Variables
```bash
# Embedding model configuration
OPENAI_API_KEY=sk-...
EMBEDDING_MODEL=text-embedding-ada-002
EMBEDDING_DIMENSION=1536

# Metadata storage
METADATA_STORE_TYPE=json  # or 'postgres', 'redis'
METADATA_STORE_PATH=./metadata/store.json

# Search configuration
SIMILARITY_THRESHOLD=0.8
MAX_CONTEXT_ENTITIES=30
CRITICALITY_THRESHOLD=7.0
```

### Criticality Scoring Formula
```
criticality = (
    usage_frequency * 0.3 +
    affects_external_api * 2.0 +
    security_sensitive * 3.0 +
    data_integrity * 2.0 +
    dependency_count * 0.1
) / 10
```

## Example Usage

### Generate Metadata for Function
```python
from services.review_bot.metadata import MetadataGenerator

generator = MetadataGenerator(neo4j_client, repo_path)
metadata = generator.generate_metadata({
    "name": "calculateTotal",
    "file_path": "src/libs/ReportUtils.ts",
    "start_line": 100,
    "end_line": 150
})
```

### Search Similar Functions
```python
from services.review_bot.metadata import SemanticSearchEngine

search = SemanticSearchEngine(metadata_store)
similar_functions = search.find_similar(
    "calculateTotal",
    threshold=0.85,
    top_k=10
)
```

### Build Smart Context
```python
from services.review_bot.metadata import SmartContextBuilder

builder = SmartContextBuilder(metadata_store, search_engine)
smart_context = builder.build_context(
    dependency_results,  # 9,591 entities
    max_entities=30,
    strategy="criticality_first"
)
# Returns ~30 most relevant entities with explanations
```

## Monitoring & Metrics

### Key Metrics to Track

1. **Metadata Coverage**: % of functions with complete metadata
2. **Search Accuracy**: Precision/recall of semantic search
3. **Context Reduction**: Ratio of filtered vs total entities
4. **Review Efficiency**: Time saved in PR reviews
5. **False Positive Rate**: Irrelevant entities included

### Performance Targets

- Metadata generation: < 10ms per function
- Semantic search: < 100ms for 10k functions
- Context building: < 500ms for 10k entities
- Storage overhead: < 1KB per function

## Future Enhancements

1. **Multi-language Support**: Extend beyond JavaScript/TypeScript
2. **Custom Domain Models**: Train domain-specific embeddings
3. **Learning System**: Improve based on reviewer feedback
4. **Real-time Updates**: Stream metadata updates
5. **Advanced Analytics**: Codebase health metrics

## Conclusion

The Semantic Metadata Search & Enrichment System transforms our code review bot from a syntactic dependency analyzer to an intelligent, context-aware review assistant. By combining static analysis, semantic understanding, and usage patterns, we can reduce the review scope by 99% while maintaining high accuracy and relevance.

This system enables:
- **Efficient PR reviews** with focused, relevant context
- **Semantic code discovery** across large codebases
- **Intelligent risk assessment** for code changes
- **Business-aware impact analysis**

The metadata enrichment layer is the key to scaling code review automation for enterprise codebases.