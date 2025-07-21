# PR Analysis Workflow

## Overview

The PR analysis workflow takes a GitHub pull request and determines which parts of the codebase are affected by the changes. It uses two levels of analysis: basic diff analysis and enhanced line-level analysis for precision.

## Workflow Stages

```
1. Fetch PR Data from GitHub
        ↓
2. Basic Diff Analysis
        ↓
3. Enhanced Line-Level Analysis
        ↓
4. Mini KG Generation
        ↓
5. Dependency Resolution
        ↓
6. Impact Assessment
```

## Stage Details

### 1. Fetch PR Data from GitHub

The system uses the GitHub API to fetch:
- List of changed files
- File additions/deletions count
- Diff patches for each file
- File contents (before and after)

Example PR data structure:
```python
{
    'filename': 'src/libs/ReportUtils.ts',
    'status': 'modified',  # added/modified/deleted
    'additions': 45,
    'deletions': 1,
    'patch': '@@ -1124,7 +1124,7 @@...',
    'contents_url': 'https://api.github.com/repos/...'
}
```

### 2. Basic Diff Analysis

The `PRDiffAnalyzer` performs initial analysis:

#### File Change Detection
```python
FileChange(
    file_path='src/libs/ReportUtils.ts',
    change_type=ChangeType.MODIFIED,
    additions=45,
    deletions=1,
    patch='@@ -1124,7 +1124,7 @@...'
)
```

#### Entity Comparison
- Extracts entities from old version (before PR)
- Extracts entities from new version (after PR)
- Compares to find:
  - Added functions/classes
  - Modified functions/classes
  - Deleted functions/classes

### 3. Enhanced Line-Level Analysis

The `EnhancedDiffAnalyzer` provides precision:

#### Diff Patch Parsing
Parses git diff hunks to extract exact line changes:
```
@@ -1124,7 +1124,7 @@ function getCurrentUserAvatar() {
-    return currentUser?.avatar;
+    return currentUser?.avatar || defaultAvatar;
 }
```

Results in:
```python
LineChange(
    line_number=1125,
    change_type='-',
    content='    return currentUser?.avatar;'
)
LineChange(
    line_number=1125,
    change_type='+',
    content='    return currentUser?.avatar || defaultAvatar;'
)
```

#### Function Mapping
Maps changed lines to containing functions:
```python
# Function spans lines 1124-1126
# Changed line 1125 is within this range
# Therefore: getCurrentUserAvatar() is modified
```

### 4. Mini KG Generation

Creates a focused knowledge graph of just the changes:

#### Mini KG Structure
```json
{
  "nodes": {
    "files": [
      {
        "path": "src/libs/ReportUtils.ts",
        "change_type": "modified",
        "additions": 1,
        "deletions": 1
      }
    ],
    "functions": [
      {
        "name": "getCurrentUserAvatar",
        "file_path": "src/libs/ReportUtils.ts",
        "start_line": 1124,
        "end_line": 1126,
        "change_type": "modified"
      }
    ]
  },
  "relationships": {
    "contains": [
      {
        "source": "src/libs/ReportUtils.ts",
        "target": "getCurrentUserAvatar",
        "type": "contains"
      }
    ]
  }
}
```

### 5. Example: PR #65748 Analysis

Let's trace through the actual PR #65748:

#### Changed Files
1. `src/libs/ReportUtils.ts` - 1 line modified
2. `tests/unit/ReportUtilsTest.ts` - 44 lines added (new tests)

#### Enhanced Analysis Results
```python
enhanced_function_changes = []  # No functions actually changed!
```

Why? The change was to a comment/type definition, not within any function body.

#### Impact Analysis
Even though no functions changed, the system still analyzes:
- Which files import `ReportUtils.ts`
- Which functions might be affected by the module change

## Key Features

### Line-Level Precision

**Traditional Approach:**
- File `ReportUtils.ts` changed → All 200+ functions marked as changed
- Massive false positive rate

**Enhanced Approach:**
- Parse actual diff lines
- Map to specific functions
- Only mark truly changed functions

### Smart Change Detection

The system distinguishes between:
1. **Actual code changes**: Modified function logic
2. **Signature changes**: Changed parameters/return types
3. **Comment changes**: Documentation updates
4. **Whitespace changes**: Formatting only

### Performance Metrics

For PR #65748:
- Files analyzed: 2
- Traditional detection: Would mark 200+ functions
- Enhanced detection: 0 functions (correct - only comments changed)
- Analysis time: ~2 seconds

## Usage

### Command Line
```bash
python services/review_bot/examples/example_pr_mini_kg.py 65748
```

### Programmatic
```python
from services.review_bot.analysis.enhanced_diff_analyzer import EnhancedDiffAnalyzer

# Initialize analyzer
analyzer = EnhancedDiffAnalyzer()

# Analyze a PR
result = analyzer.analyze_pr_with_line_diffs(65748)

# Access results
print(f"Files changed: {len(result['file_changes'])}")
print(f"Functions changed: {len(result['enhanced_function_changes'])}")

# Get specific function changes
for func in result['enhanced_function_changes']:
    print(f"{func['name']} in {func['file_path']} (lines {func['new_lines']})")
```

## Output Format

The complete analysis produces:
```json
{
  "pr_number": 65748,
  "summary": {
    "total_files_changed": 2,
    "files_added": 0,
    "files_modified": 2,
    "files_deleted": 0,
    "enhanced_functions_changed": 0
  },
  "file_changes": [...],
  "function_changes": [...],
  "enhanced_function_changes": [...],
  "mini_kg": {
    "nodes": {...},
    "relationships": {...}
  }
}
```

## Integration with Dependency Analysis

The PR analysis output feeds directly into dependency analysis:
1. Enhanced function changes → Query for direct callers
2. Changed files → Query for importing files
3. Mini KG → Context for impact assessment

## Error Handling

Common scenarios handled:
- **Large diffs**: Gracefully handle massive PRs
- **Binary files**: Skip non-text files
- **Merge conflicts**: Parse complex diffs
- **API rate limits**: Retry with backoff

## Future Enhancements

1. **Type change detection**: Identify when interfaces/types change
2. **Semantic diff**: Understand logical changes beyond syntax
3. **Test impact**: Link changed code to affected tests
4. **Performance optimization**: Parallel diff processing