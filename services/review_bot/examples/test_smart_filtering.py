"""
Test script to evaluate smart KG query filtering performance.
This script tests the new smart filtering approach against PR 65748.
"""

import json
import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from libs.neo4j_client import Neo4jClient
from services.review_bot.analysis import DependencyResolver
from services.review_bot.config import ReviewBotConfig


def load_test_data():
    """Load the PR 65748 test data."""
    test_data_path = Path(__file__).parent.parent / "outputs" / "mini_kg_pr_65748.json"
    
    if not test_data_path.exists():
        print(f"❌ Test data not found at {test_data_path}")
        return None
    
    with open(test_data_path) as f:
        return json.load(f)


def test_smart_filtering():
    """Test the smart filtering approach."""
    print("🧪 Testing Smart KG Query Filtering")
    print("=" * 50)
    
    # Load test data
    test_data = load_test_data()
    if not test_data:
        return
    
    mini_kg = test_data["mini_kg"]
    print(f"📊 Test case: PR 65748 with {len(mini_kg['nodes']['files'])} changed files")
    
    # Initialize Neo4j client
    neo4j_config = ReviewBotConfig.get_neo4j_config()
    neo4j_client = Neo4jClient(
        uri=neo4j_config["uri"],
        user=neo4j_config["user"],
        password=neo4j_config["password"]
    )
    
    try:
        # Connect to Neo4j
        neo4j_client.connect()
        print("✅ Connected to Neo4j")
        
        # Initialize dependency resolver
        resolver = DependencyResolver(neo4j_client)
        
        # Test the smart filtering
        print("\n🔍 Running dependency analysis with smart filtering...")
        start_time = time.time()
        
        results = resolver.analyze_dependencies(mini_kg)
        
        end_time = time.time()
        
        # Print results
        print(f"\n📈 Results (took {end_time - start_time:.2f} seconds):")
        print("=" * 30)
        
        summary = results["summary"]
        print(f"Direct impacts: {summary['direct_impacts']}")
        print(f"Secondary impacts: {summary['secondary_impacts']}")
        print(f"Total impacted: {summary['total_impacted']}")
        
        # Analyze filtering effectiveness
        print("\n🎯 Filtering Analysis:")
        print("=" * 25)
        
        # Check if we reduced the secondary impacts
        if summary['secondary_impacts'] < 9000:  # Previously was 9,568
            reduction = 9568 - summary['secondary_impacts']
            percentage = (reduction / 9568) * 100
            print(f"✅ Reduction: {reduction} entities ({percentage:.1f}%)")
            print("   Before: 9,568 secondary impacts")
            print(f"   After:  {summary['secondary_impacts']} secondary impacts")
        else:
            print("❌ No significant reduction achieved")
        
        # Analyze filtering strategies
        print("\n🧠 Filtering Strategy Breakdown:")
        print("=" * 35)
        
        # Count functions by filter reason
        filter_counts = {"actual_usage": 0, "high_centrality": 0, "orchestrator": 0}
        
        for impacts in results["impacts"].values():
            for func in impacts.get("secondary", []):
                filter_reason = func.get("filter_reason", "unknown")
                if filter_reason in filter_counts:
                    filter_counts[filter_reason] += 1
        
        for reason, count in filter_counts.items():
            print(f"   {reason}: {count} functions")
        
        # Show sample results
        print("\n📋 Sample Filtered Functions:")
        print("=" * 30)
        
        sample_functions = []
        for impacts in results["impacts"].values():
            sample_functions.extend(impacts.get("secondary", [])[:10])
        
        for i, func in enumerate(sample_functions[:5]):
            reason = func.get("filter_reason", "unknown")
            print(f"   {i+1}. {func['name']} ({reason})")
            if reason == "actual_usage":
                print(f"      → Calls: {func.get('called_function', 'N/A')}")
            elif reason == "high_centrality":
                print(f"      → Incoming calls: {func.get('incoming_calls', 'N/A')}")
            elif reason == "orchestrator":
                print(f"      → Outgoing calls: {func.get('outgoing_calls', 'N/A')}")
        
        # Save results for comparison
        output_path = Path(__file__).parent.parent / "outputs" / "smart_filtering_results.json"
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n💾 Results saved to: {output_path}")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        if hasattr(neo4j_client, 'close'):
            neo4j_client.close()
        elif hasattr(neo4j_client, 'disconnect'):
            neo4j_client.disconnect()


if __name__ == "__main__":
    test_smart_filtering()