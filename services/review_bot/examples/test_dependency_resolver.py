"""
Test script for dependency resolver - demonstrates finding impacted entities from main KG.
This combines the PR diff analyzer with dependency resolution.
"""

import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from services.review_bot.analysis import PRDiffAnalyzer, DependencyResolver
from libs.neo4j_client import Neo4jClient
from services.review_bot.config import ReviewBotConfig


def print_dependency_analysis(result: dict):
    """Print detailed dependency analysis results."""
    
    print("\n🔗 Dependency Analysis Results:")
    print("=" * 60)
    
    # Summary
    summary = result["summary"]
    print(f"\n📊 Summary:")
    print(f"   Total impacted entities: {summary['total_impacted']}")
    print(f"   - Direct impacts: {summary['direct_impacts']}")
    print(f"   - Secondary impacts: {summary['secondary_impacts']}")
    print(f"   - Tertiary impacts: {summary['tertiary_impacts']}")
    
    print(f"\n📈 By Entity Type:")
    for entity_type, count in summary["entity_counts"].items():
        if count > 0:
            print(f"   - {entity_type.title()}s: {count}")
    
    print(f"\n⚠️ By Risk Level:")
    for risk_level, count in summary["risk_counts"].items():
        if count > 0:
            print(f"   - {risk_level.title()}: {count}")
    
    # Changed entities
    changed = result["changed_entities"]
    print(f"\n🔄 Changed Entities ({len(changed)}):")
    for entity in changed[:5]:  # Show first 5
        print(f"   {entity['change_type']}: {entity['name']} ({entity['type']}) in {entity['file_path']}")
    if len(changed) > 5:
        print(f"   ... and {len(changed) - 5} more")
    
    # Dependency chains
    chains = result["dependency_chains"]
    if chains:
        print(f"\n🔗 Dependency Chains (showing first 10 of {len(chains)}):")
        for chain in chains[:10]:
            risk_emoji = "🔴" if chain["risk_level"] == "high" else "🟡" if chain["risk_level"] == "medium" else "🟢"
            print(f"   {risk_emoji} {chain['source']} → {chain['target']} ({chain['relationship']}, {chain['length']}-hop)")
    
    # Sample impacts
    impacts = result["impacts"]
    if impacts:
        print(f"\n💥 Sample Direct Impacts:")
        for entity_key, entity_impacts in list(impacts.items())[:3]:
            direct_impacts = entity_impacts.get("direct", [])
            if direct_impacts:
                print(f"   {entity_key}:")
                for impact in direct_impacts[:3]:
                    print(f"     → {impact['name']} in {impact['file_path']} ({impact['relationship_type']})")
                if len(direct_impacts) > 3:
                    print(f"     ... and {len(direct_impacts) - 3} more")


def main():
    """
    Test the complete flow: PR analysis + dependency resolution.
    
    Usage: python test_dependency_resolver.py [PR_NUMBER]
    """
    
    # Get PR number from command line or use default
    if len(sys.argv) > 1:
        pr_number = int(sys.argv[1])
    else:
        pr_number = 65748  # Default test PR
        print(f"ℹ️  No PR number provided, using default: {pr_number}")
        print(f"   Usage: python {sys.argv[0]} <PR_NUMBER>")
    
    print(f"\n🚀 Testing Complete PR Analysis + Dependency Resolution")
    print(f"🎯 PR: #{pr_number}")
    print("=" * 70)
    
    try:
        # Step 1: Analyze PR to get mini KG
        print("\n📋 Step 1: Analyzing PR changes...")
        analyzer = PRDiffAnalyzer()
        pr_result = analyzer.analyze_pr(pr_number)
        
        if not pr_result["file_changes"]:
            print("❌ No file changes found in PR - cannot proceed with dependency analysis")
            return
        
        mini_kg = pr_result["mini_kg"]
        print(f"✅ Mini KG built with {len(mini_kg['changes']['added_functions']) + len(mini_kg['changes']['modified_functions'])} function changes")
        
        # Step 2: Connect to Neo4j and resolve dependencies
        print("\n📋 Step 2: Connecting to main knowledge graph...")
        neo4j_config = ReviewBotConfig.get_neo4j_config()
        neo4j_client = Neo4jClient(
            uri=neo4j_config["uri"],
            user=neo4j_config["user"], 
            password=neo4j_config["password"]
        )
        
        success, message = neo4j_client.connect()
        if not success:
            print(f"❌ Failed to connect to Neo4j: {message}")
            print("💡 Make sure Neo4j is running and the main KG has been built")
            return
        
        print(f"✅ {message}")
        
        # Step 3: Resolve dependencies
        print("\n📋 Step 3: Resolving dependencies...")
        resolver = DependencyResolver(neo4j_client)
        dependency_result = resolver.analyze_dependencies(mini_kg)
        
        # Step 4: Display results
        print_dependency_analysis(dependency_result)
        
        # Step 5: Save combined results
        combined_result = {
            "pr_analysis": pr_result,
            "dependency_analysis": dependency_result,
            "metadata": {
                "pr_number": pr_number,
                "analysis_type": "complete_flow"
            }
        }
        
        # Save to outputs directory
        outputs_dir = Path(__file__).parent.parent / "outputs"
        outputs_dir.mkdir(exist_ok=True)
        output_file = outputs_dir / f"complete_analysis_pr_{pr_number}.json"
        
        with open(output_file, 'w') as f:
            json.dump(combined_result, f, indent=2)
        print(f"\n💾 Complete analysis saved to: {output_file}")
        
        # Step 6: Next steps
        print(f"\n🎯 What This Tells Us:")
        if dependency_result["summary"]["total_impacted"] > 0:
            print("   ✅ Successfully found impacted entities in main KG")
            print("   ✅ Dependency resolution is working")
            print("   📝 Ready for context building (smart code fetching)")
        else:
            print("   ⚠️  No impacted entities found")
            print("   💡 This could mean:")
            print("      - The main KG doesn't have these entities")
            print("      - The PR changes are isolated (no dependencies)")
            print("      - The Neo4j queries need refinement")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        if 'neo4j_client' in locals():
            neo4j_client.disconnect()


if __name__ == "__main__":
    main()