"""
Enhanced PR Analysis Script - Complete Pipeline

This script provides end-to-end PR analysis using:
1. Enhanced Diff Analyzer for line-level change detection  
2. Dependency analysis for impact assessment
3. Complete JSON output for review

Usage: python example_pr_mini_kg.py <PR_NUMBER>
"""

import sys
import json
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from services.review_bot.analysis.enhanced_diff_analyzer import EnhancedDiffAnalyzer
from services.review_bot.analysis import DependencyResolver
from services.review_bot.config import ReviewBotConfig
from libs.neo4j_client import Neo4jClient


def print_enhanced_analysis_summary(result: dict):
    """Print enhanced analysis summary with key metrics."""
    
    print("\n📊 Enhanced PR Analysis Summary:")
    print("=" * 50)
    
    # Basic PR info
    summary = result["summary"]
    print(f"\n📈 PR Summary:")
    print(f"   Files: {summary['total_files_changed']} changed "
          f"(+{summary['files_added']} ~{summary['files_modified']} -{summary['files_deleted']})")
    print(f"   Lines: +{summary['total_additions']} -{summary['total_deletions']}")
    
    # Enhanced function changes
    enhanced_changes = result.get("enhanced_function_changes", [])
    if enhanced_changes:
        print(f"\n🎯 Enhanced Function Detection:")
        print(f"   Functions with actual changes: {len(enhanced_changes)}")
        for change in enhanced_changes:
            lines_info = f" (lines: {change.get('changed_lines', 'N/A')})" if change.get('changed_lines') else ""
            print(f"   ✅ {change['name']} in {change['file_path']}{lines_info}")
    else:
        print(f"\n⚠️  No enhanced function changes detected - using file-level fallback")
        
    # Mini KG structure  
    mini_kg = result["mini_kg"]
    nodes = mini_kg["nodes"]
    relationships = mini_kg["relationships"]
    
    print(f"\n🌐 Mini KG Structure:")
    print(f"   Nodes: {len(nodes['files'])} files, {len(nodes['functions'])} functions")
    print(f"   Relationships: {len(relationships['calls'])} calls, {len(relationships['contains'])} contains")


def print_dependency_analysis_summary(dep_results: dict):
    """Print dependency analysis results summary."""
    
    print(f"\n🔗 Dependency Impact Analysis:")
    print("=" * 50)
    
    # Changed entities
    changed_entities = dep_results.get("changed_entities", [])
    print(f"\n📍 Changed Entities: {len(changed_entities)}")
    for entity in changed_entities:
        detection = entity.get("detection_method", "file_level")
        print(f"   • {entity['name']} ({entity['type']}) - {detection}")
    
    # Impact summary
    impacts = dep_results.get("impacts", {})
    total_direct = sum(len(entity_impacts.get("direct", [])) for entity_impacts in impacts.values())
    total_secondary = sum(len(entity_impacts.get("secondary", [])) for entity_impacts in impacts.values())
    
    print(f"\n📊 Impact Summary:")
    print(f"   Direct impacts: {total_direct}")
    print(f"   Secondary impacts: {total_secondary}")
    print(f"   Total impacts: {total_direct + total_secondary}")
    
    # Show key impacted functions
    print(f"\n🎯 Key Impacts (sample):")
    impact_count = 0
    for entity_key, entity_impacts in impacts.items():
        if impact_count >= 5:
            break
        print(f"   {entity_key}:")
        for impact in entity_impacts.get("direct", [])[:3]:
            print(f"     → {impact.get('name', 'N/A')} ({impact.get('relationship_type', 'N/A')})")
        impact_count += 1


def main():
    """
    Enhanced PR Analysis - Complete Pipeline
    
    Usage: python example_pr_mini_kg.py <PR_NUMBER>
    """
    
    # Get PR number from command line
    if len(sys.argv) > 1:
        pr_number = int(sys.argv[1])
    else:
        print(f"❌ Usage: python {sys.argv[0]} <PR_NUMBER>")
        print(f"   Example: python {sys.argv[0]} 65748")
        sys.exit(1)
    
    print(f"🚀 Enhanced PR Analysis Pipeline for PR #{pr_number}")
    print("=" * 60)
    print(f"🎯 Using line-level diff analysis for precision")
    print(f"🔗 Including dependency impact analysis")
    
    start_time = time.time()
    
    try:
        # Step 1: Enhanced Diff Analysis
        print(f"\n📍 Step 1: Enhanced Diff Analysis...")
        analyzer = EnhancedDiffAnalyzer()
        result = analyzer.analyze_pr_with_line_diffs(pr_number)
        
        print(f"✅ Enhanced analysis completed!")
        print_enhanced_analysis_summary(result)
        
        # Step 2: Dependency Analysis  
        print(f"\n📍 Step 2: Dependency Impact Analysis...")
        
        # Initialize Neo4j client
        neo4j_config = ReviewBotConfig.get_neo4j_config()
        neo4j_client = Neo4jClient(
            neo4j_config["uri"], 
            neo4j_config["user"], 
            neo4j_config["password"]
        )
        
        # Connect to Neo4j
        connected, message = neo4j_client.connect()
        if not connected:
            print(f"❌ Neo4j connection failed: {message}")
            print("💡 Make sure Neo4j is running and main KG is built")
            sys.exit(1)
        print(f"✅ Neo4j connected: {message}")
        
        # Initialize dependency resolver
        resolver = DependencyResolver(neo4j_client)
        
        # Prepare enhanced mini_kg for dependency analysis
        enhanced_mini_kg = result["mini_kg"].copy()
        enhanced_mini_kg["enhanced_function_changes"] = result.get("enhanced_function_changes", [])
        
        # Run dependency analysis
        dependency_results = resolver.analyze_dependencies(enhanced_mini_kg)
        
        print(f"✅ Dependency analysis completed!")
        print_dependency_analysis_summary(dependency_results)
        
        # Step 3: Generate Separate Output Files
        print(f"\n📍 Step 3: Generating Separate Output Files...")
        
        outputs_dir = Path(__file__).parent.parent / "outputs"
        outputs_dir.mkdir(exist_ok=True)
        
        # 1. Mini KG Output (Enhanced Diff Analysis + Mini KG)
        mini_kg_result = {
            "pr_number": pr_number,
            "analysis_timestamp": time.time(),
            "file_changes": result["file_changes"],
            "enhanced_function_changes": result.get("enhanced_function_changes", []),
            "mini_kg": result["mini_kg"],
            "summary": result["summary"]
        }
        
        mini_kg_file = outputs_dir / f"mini_kg_pr_{pr_number}.json"
        with open(mini_kg_file, 'w') as f:
            json.dump(mini_kg_result, f, indent=2)
        
        print(f"💾 Mini KG saved to: {mini_kg_file}")
        
        # 2. Dependency Analysis Output (With Same-File Filtering)
        dependency_analysis_result = {
            "pr_number": pr_number,
            "analysis_timestamp": time.time(),
            "changed_entities": dependency_results["changed_entities"],
            "impacts": dependency_results["impacts"],
            "dependency_chains": dependency_results["dependency_chains"],
            "summary": dependency_results["summary"],
            "filtering_applied": {
                "intelligent_same_file_filtering": True,
                "description": "Same-file functions are intelligently filtered: keeps direct callers of changed functions (preserves call chains) but removes non-calling same-file functions (reduces noise)"
            }
        }
        
        dependency_file = outputs_dir / f"dependency_analysis_pr_{pr_number}.json"
        with open(dependency_file, 'w') as f:
            json.dump(dependency_analysis_result, f, indent=2)
        
        print(f"💾 Dependency analysis saved to: {dependency_file}")
        
        # 3. Combined Output (for backward compatibility)
        final_result = {
            "pr_number": pr_number,
            "analysis_timestamp": time.time(),
            "enhanced_diff_analysis": result,
            "dependency_analysis": dependency_results,
            "performance_metrics": {
                "total_analysis_time_seconds": time.time() - start_time,
                "functions_with_changes": len(result.get("enhanced_function_changes", [])),
                "total_impacts": sum(len(impacts.get("direct", [])) + len(impacts.get("secondary", [])) 
                                   for impacts in dependency_results.get("impacts", {}).values())
            }
        }
        
        combined_file = outputs_dir / f"enhanced_pr_analysis_{pr_number}.json"
        with open(combined_file, 'w') as f:
            json.dump(final_result, f, indent=2)
        
        print(f"💾 Combined analysis saved to: {combined_file}")
        
        # Performance summary
        duration = time.time() - start_time
        print(f"\n🎉 Analysis Complete!")
        print(f"⏱️  Total time: {duration:.2f} seconds")
        print(f"🎯 Functions analyzed: {len(result.get('enhanced_function_changes', []))} (enhanced detection)")
        print(f"📊 Total impacts: {final_result['performance_metrics']['total_impacts']}")
        
        # Call chain validation for specific functions
        if result.get("enhanced_function_changes"):
            print(f"\n🔍 Call Chain Validation:")
            for change in result["enhanced_function_changes"]:
                func_name = change["name"]
                print(f"   Changed: {func_name}")
                
                # Look for this function in impacts
                for entity_key, impacts in dependency_results.get("impacts", {}).items():
                    if func_name in entity_key:
                        direct_callers = [imp["name"] for imp in impacts.get("direct", []) 
                                        if imp.get("relationship_type") == "calls"][:3]
                        if direct_callers:
                            print(f"   → Direct callers: {', '.join(direct_callers)}")
                        break
        
        # Close Neo4j connection
        neo4j_client.disconnect()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()