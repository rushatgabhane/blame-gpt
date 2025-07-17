"""
Example: Build a mini knowledge graph from a PR's changes.
This demonstrates step 1 of the review bot - analyzing PR diffs.
"""

import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from services.review_bot.analysis import PRDiffAnalyzer


def print_mini_kg_details(mini_kg: dict):
    """Print detailed information about the mini KG."""
    
    print("\n📊 Mini Knowledge Graph Details:")
    print("=" * 50)
    
    # Changes summary
    changes = mini_kg["changes"]
    print("\n🔄 Changes Summary:")
    if changes["added_files"]:
        print(f"   Added Files ({len(changes['added_files'])}):")
        for f in changes["added_files"][:3]:
            print(f"     + {f}")
        if len(changes["added_files"]) > 3:
            print(f"     ... and {len(changes['added_files']) - 3} more")
    
    if changes["modified_files"]:
        print(f"   Modified Files ({len(changes['modified_files'])}):")
        for f in changes["modified_files"][:3]:
            print(f"     ~ {f}")
        if len(changes["modified_files"]) > 3:
            print(f"     ... and {len(changes['modified_files']) - 3} more")
    
    if changes["deleted_files"]:
        print(f"   Deleted Files ({len(changes['deleted_files'])}):")
        for f in changes["deleted_files"][:3]:
            print(f"     - {f}")
        if len(changes["deleted_files"]) > 3:
            print(f"     ... and {len(changes['deleted_files']) - 3} more")
    
    # Function changes
    print("\n🔧 Function Changes:")
    for change_type in ["added_functions", "modified_functions", "deleted_functions"]:
        if changes[change_type]:
            print(f"   {change_type.replace('_', ' ').title()} ({len(changes[change_type])}):")
            for func in changes[change_type][:3]:
                print(f"     {'+'if 'added' in change_type else '~' if 'modified' in change_type else '-'} {func['name']} in {func['file_path']}")
            if len(changes[change_type]) > 3:
                print(f"     ... and {len(changes[change_type]) - 3} more")
    
    # Graph structure
    print("\n🌐 Graph Structure:")
    nodes = mini_kg["nodes"]
    print(f"   Nodes:")
    print(f"     - Files: {len(nodes['files'])}")
    print(f"     - Functions: {len(nodes['functions'])}")
    print(f"     - Classes: {len(nodes['classes'])}")
    print(f"     - Imports: {len(nodes['imports'])}")
    
    relationships = mini_kg["relationships"]
    print(f"   Relationships:")
    print(f"     - Contains: {len(relationships['contains'])}")
    print(f"     - Imports: {len(relationships['imports'])}")
    print(f"     - Calls: {len(relationships['calls'])}")
    
    # Sample imports
    if nodes["imports"]:
        print("\n📦 Sample Imports:")
        for imp in nodes["imports"][:5]:
            print(f"   {imp['file_path']} imports {imp['module']}")
        if len(nodes["imports"]) > 5:
            print(f"   ... and {len(nodes['imports']) - 5} more")
    
    # Sample function calls
    if relationships["calls"]:
        print("\n📞 Sample Function Calls:")
        for call in relationships["calls"][:5]:
            print(f"   {call['source']}:{call['line']} calls {call['target']}")
        if len(relationships["calls"]) > 5:
            print(f"   ... and {len(relationships['calls']) - 5} more")


def main():
    """
    Example of building a mini KG from a PR.
    
    Usage: python example_pr_mini_kg.py [PR_NUMBER]
    """
    
    # Get PR number from command line or use default
    if len(sys.argv) > 1:
        pr_number = int(sys.argv[1])
    else:
        # You should replace this with an actual PR number from your repo
        pr_number = 1  
        print(f"ℹ️  No PR number provided, using default: {pr_number}")
        print(f"   Usage: python {sys.argv[0]} <PR_NUMBER>")
    
    print(f"\n🚀 Building Mini Knowledge Graph for PR #{pr_number}")
    print("=" * 60)
    
    # Initialize analyzer
    analyzer = PRDiffAnalyzer()
    
    try:
        # Analyze the PR
        result = analyzer.analyze_pr(pr_number)
        
        # Print summary
        summary = result["summary"]
        print(f"\n✅ PR Analysis Complete!")
        print(f"\n📈 Summary:")
        print(f"   Files: {summary['total_files_changed']} changed "
              f"(+{summary['files_added']} ~{summary['files_modified']} -{summary['files_deleted']})")
        print(f"   Functions: {summary['total_functions_changed']} changed "
              f"(+{summary['functions_added']} ~{summary['functions_modified']} -{summary['functions_deleted']})")
        print(f"   Lines: +{summary['total_additions']} -{summary['total_deletions']}")
        
        # Print mini KG details
        print_mini_kg_details(result["mini_kg"])
        
        # Save to file in outputs directory
        outputs_dir = Path(__file__).parent.parent / "outputs"
        outputs_dir.mkdir(exist_ok=True)  # Create outputs dir if it doesn't exist
        output_file = outputs_dir / f"mini_kg_pr_{pr_number}.json"
        
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"\n💾 Mini KG saved to: {output_file}")
        
        print("\n🎯 Next Steps:")
        print("   1. Use this mini KG to query the main KG for dependencies")
        print("   2. Build context with impacted files and functions")
        print("   3. Send enriched context to LLM for review")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()