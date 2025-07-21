#!/usr/bin/env python3
"""
Extract just the changed_entities section from the smart filtering results.
"""

import json
from pathlib import Path

def extract_changed_entities():
    """Extract and save just the changed entities."""
    input_file = Path(__file__).parent / "smart_filtering_results.json"
    output_file = Path(__file__).parent / "changed_entities_only.json"
    
    print(f"Reading from: {input_file}")
    
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    # Extract just the changed entities
    changed_entities = data.get("changed_entities", [])
    
    # Create a summary
    summary = {
        "total_changed_entities": len(changed_entities),
        "by_type": {},
        "by_change_type": {}
    }
    
    for entity in changed_entities:
        entity_type = entity.get("type", "unknown")
        change_type = entity.get("change_type", "unknown")
        
        summary["by_type"][entity_type] = summary["by_type"].get(entity_type, 0) + 1
        summary["by_change_type"][change_type] = summary["by_change_type"].get(change_type, 0) + 1
    
    # Create output structure
    output = {
        "summary": summary,
        "changed_entities": changed_entities
    }
    
    print(f"Writing to: {output_file}")
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"✅ Successfully extracted {len(changed_entities)} changed entities")
    print(f"📊 Summary:")
    print(f"   By Type: {summary['by_type']}")
    print(f"   By Change Type: {summary['by_change_type']}")

if __name__ == "__main__":
    extract_changed_entities()