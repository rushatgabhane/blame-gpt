"""
Test script for PR diff analyzer - demonstrates building mini KG from PR changes.
"""

import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from services.review_bot.analysis import PRDiffAnalyzer


def main():
    """Test the PR diff analyzer with a sample PR."""
    
    # You can change this to test with different PRs
    pr_number = 123  # Replace with actual PR number
    
    print(f"🚀 Testing PR Diff Analyzer with PR #{pr_number}")
    print("=" * 60)
    
    # Initialize analyzer
    analyzer = PRDiffAnalyzer()
    
    try:
        # Analyze the PR
        result = analyzer.analyze_pr(pr_number)
        
        # Print summary
        print("\n📊 PR Analysis Summary:")
        summary = result["summary"]
        print(f"   Total files changed: {summary['total_files_changed']}")
        print(f"   - Added: {summary['files_added']}")
        print(f"   - Modified: {summary['files_modified']}")
        print(f"   - Deleted: {summary['files_deleted']}")
        print(f"\n   Total functions changed: {summary['total_functions_changed']}")
        print(f"   - Added: {summary['functions_added']}")
        print(f"   - Modified: {summary['functions_modified']}")
        print(f"   - Deleted: {summary['functions_deleted']}")
        print(f"\n   Lines: +{summary['total_additions']} -{summary['total_deletions']}")
        
        # Print file changes
        print("\n📁 File Changes:")
        for fc in result["file_changes"]:
            print(f"   {fc['change_type']}: {fc['file_path']} (+{fc['additions']} -{fc['deletions']})")
        
        # Print function changes
        if result["function_changes"]:
            print("\n🔧 Function Changes:")
            for fc in result["function_changes"]:
                print(f"   {fc['change_type']}: {fc['name']} in {fc['file_path']}")
        
        # Print mini KG structure
        mini_kg = result["mini_kg"]
        print("\n🌐 Mini Knowledge Graph:")
        print(f"   Nodes:")
        print(f"   - Files: {len(mini_kg['nodes']['files'])}")
        print(f"   - Functions: {len(mini_kg['nodes']['functions'])}")
        print(f"   - Classes: {len(mini_kg['nodes']['classes'])}")
        print(f"   - Imports: {len(mini_kg['nodes']['imports'])}")
        print(f"\n   Relationships:")
        print(f"   - Contains: {len(mini_kg['relationships']['contains'])}")
        print(f"   - Imports: {len(mini_kg['relationships']['imports'])}")
        print(f"   - Calls: {len(mini_kg['relationships']['calls'])}")
        
        # Save full result to file for inspection
        output_file = f"pr_{pr_number}_analysis.json"
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"\n💾 Full analysis saved to: {output_file}")
        
    except Exception as e:
        print(f"\n❌ Error analyzing PR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()