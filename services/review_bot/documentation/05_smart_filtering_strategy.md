# Smart Filtering Strategy

## The Problem

When analyzing pull request impacts in large codebases, a single file change can cascade through imports to affect thousands of functions. For example:

```
ReportUtils.ts changed
    ↓
100 files import ReportUtils.ts
    ↓
Each file has ~50 functions
    ↓
5,000 potential impacts! 😱
```

Most of these "impacts" are false positives - functions that import the module but never use the changed code.

## The Solution: Three-Pronged Smart Filtering

The review bot implements intelligent filtering to identify truly relevant impacts:

```
┌─────────────────────────────────────────────────┐
│          Smart Filtering Strategies             │
├─────────────────────────────────────────────────┤
│                                                 │
│  1. Actual Usage     🎯 Highest Priority       │
│     Functions that directly call changed code   │
│                                                 │
│  2. High Centrality  ⭐ Medium Priority        │
│     Important functions called by many others   │
│                                                 │
│  3. Orchestrators    🎼 Lower Priority         │
│     Functions that coordinate many operations   │
│                                                 │
└─────────────────────────────────────────────────┘
```

## Strategy 1: Actual Usage Detection

### Concept
Find functions that actually call or use the changed code, not just import the file.

### Implementation
```cypher
// Direct INVOKES relationships
MATCH (caller:Function)-[:INVOKES]->(target:Function)
WHERE target.file_path ENDS WITH $changed_file

// Module-style calls
MATCH (file:File)-[:CALLS]->(fc:FunctionCall)
WHERE fc.target CONTAINS $module_name
  AND caller.start_line <= fc.line <= caller.end_line
```

### Example
```typescript
// File: OrderService.ts
import { calculateTotal, formatCurrency } from './calculations';

function processOrder(items) {
    const total = calculateTotal(items);  // ✅ Actual usage
    return total;
}

function displayOrder(order) {
    // ❌ No usage of imported functions
    console.log(order.id);
}
```

Result: Only `processOrder` is flagged, not `displayOrder`

### Benefits
- Near 100% precision for direct dependencies
- Eliminates most false positives
- Provides clear impact chains

## Strategy 2: High Centrality Detection

### Concept
Identify "hub" functions that many other functions depend on. These are critical paths in the codebase.

### Metrics
```
Centrality Score = Number of incoming function calls
Threshold = 5 (configurable)
```

### Query Pattern
```cypher
MATCH (func:Function)
OPTIONAL MATCH (caller)-[:CALLS]->(fc:FunctionCall)
WHERE fc.target = func.name
WITH func, count(fc) as incoming_calls
WHERE incoming_calls >= $min_centrality_threshold
ORDER BY incoming_calls DESC
```

### Example
```typescript
// High centrality function (called by 20+ other functions)
function validateUser(user) {
    // Core validation logic
}

// Low centrality function (called by 1-2 functions)
function formatUserGreeting(name) {
    return `Hello, ${name}!`;
}
```

### Rationale
- Central functions are critical paths
- Changes affecting them have wider impact
- Important for regression testing

## Strategy 3: Orchestrator Detection

### Concept
Find functions that coordinate many operations - they might use changed functionality indirectly.

### Metrics
```
Orchestration Score = Number of outgoing function calls
Threshold = 10 (configurable)
```

### Query Pattern
```cypher
MATCH (func:Function)
OPTIONAL MATCH (file)-[:CALLS]->(fc:FunctionCall)
WHERE func.start_line <= fc.line <= func.end_line
WITH func, count(fc) as outgoing_calls
WHERE outgoing_calls >= $min_orchestrator_threshold
ORDER BY outgoing_calls DESC
```

### Example
```typescript
// Orchestrator function (15+ outgoing calls)
async function completeCheckout(order) {
    validateOrder(order);
    calculateTaxes(order);
    applyDiscounts(order);
    processPayment(order);
    updateInventory(order);
    sendConfirmation(order);
    logTransaction(order);
    // ... more calls
}

// Simple function (2-3 calls)
function getOrderStatus(orderId) {
    const order = fetchOrder(orderId);
    return order.status;
}
```

## Priority and Combination Logic

### Priority Levels
1. **Actual Usage**: Priority 1 (Highest)
2. **High Centrality**: Priority 2 (Medium)
3. **Orchestrators**: Priority 3 (Lower)

### Combination Algorithm
```python
def combine_results(actual_usage, high_centrality, orchestrators):
    all_functions = {}
    
    # Add actual usage (highest priority)
    for func in actual_usage:
        key = f"{func['file_path']}:{func['name']}"
        func['priority'] = 1
        all_functions[key] = func
    
    # Add high centrality (if not already present)
    for func in high_centrality:
        key = f"{func['file_path']}:{func['name']}"
        if key not in all_functions:
            func['priority'] = 2
            all_functions[key] = func
    
    # Add orchestrators (if not already present)
    for func in orchestrators:
        key = f"{func['file_path']}:{func['name']}"
        if key not in all_functions:
            func['priority'] = 3
            all_functions[key] = func
    
    # Sort by priority and apply limits
    sorted_functions = sorted(all_functions.values(), 
                            key=lambda x: x['priority'])
    return sorted_functions[:MAX_SECONDARY_IMPACTS]
```

## File-Based Prioritization

### The Challenge
Even with filtering, we might have 200 relevant functions across 50 files.

### The Solution
Prioritize complete files over scattered functions:

```python
def apply_file_priority_filtering(functions, limit):
    # Group by file
    by_file = group_by_file(functions)
    
    # Sort files by number of relevant functions
    # (More functions = tighter coupling)
    file_items = sorted(by_file.items(), 
                       key=lambda x: len(x[1]), 
                       reverse=True)
    
    # Take ALL functions from high-priority files
    result = []
    for file_path, file_functions in file_items:
        if len(result) + len(file_functions) <= limit:
            result.extend(file_functions)
        else:
            break
    
    return result
```

### Benefits
- Maintains context (all related functions in a file)
- Easier for developers to review
- Better test coverage

## Configuration

### Environment Variables
```bash
# Enable/disable smart filtering
ENABLE_SMART_FILTERING=true

# Maximum number of secondary impacts to return
MAX_SECONDARY_IMPACTS=80

# Minimum incoming calls for high centrality
MIN_CENTRALITY_THRESHOLD=5

# Minimum outgoing calls for orchestrators
MIN_ORCHESTRATOR_THRESHOLD=10
```

### Tuning Guide

#### For Precision (Fewer Results)
```bash
ENABLE_SMART_FILTERING=true
MAX_SECONDARY_IMPACTS=30
MIN_CENTRALITY_THRESHOLD=10
MIN_ORCHESTRATOR_THRESHOLD=20
```

#### For Coverage (More Results)
```bash
ENABLE_SMART_FILTERING=true
MAX_SECONDARY_IMPACTS=150
MIN_CENTRALITY_THRESHOLD=3
MIN_ORCHESTRATOR_THRESHOLD=5
```

#### For Debugging (No Filtering)
```bash
ENABLE_SMART_FILTERING=false
```

## Real-World Impact

### Before Smart Filtering
- PR changes 1 file
- System reports 5,000+ impacted functions
- Developers overwhelmed, ignore results
- False positive rate: >95%

### After Smart Filtering
- PR changes 1 file
- System reports 50-80 relevant functions
- Developers can review each impact
- False positive rate: <20%

## Example Output

```json
{
  "impacts": {
    "src/libs/calculations.ts:calculateTotal": {
      "direct": [
        {
          "name": "processOrder",
          "filter_reason": "actual_usage",
          "priority": 1,
          "called_function": "calculateTotal"
        },
        {
          "name": "validateTotal",
          "filter_reason": "actual_usage", 
          "priority": 1,
          "called_function": "calculateTotal"
        },
        {
          "name": "generateReport",
          "filter_reason": "high_centrality",
          "priority": 2,
          "incoming_calls": 15
        },
        {
          "name": "executeWorkflow",
          "filter_reason": "orchestrator",
          "priority": 3,
          "outgoing_calls": 25
        }
      ]
    }
  }
}
```

## Limitations and Future Work

### Current Limitations
1. **Dynamic imports**: Not detected by static analysis
2. **Indirect usage**: Through callbacks or event handlers
3. **Type dependencies**: Interface changes not tracked

### Planned Improvements
1. **Confidence scoring**: Rate likelihood of impact
2. **Path analysis**: Show exact call chains
3. **Machine learning**: Learn from historical PR impacts
4. **Custom strategies**: Plugin architecture for domain-specific filtering