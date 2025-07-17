"""
Example usage of the knowledge graph builder for the review bot.
This script demonstrates how to build a knowledge graph from the configured GitHub repository.
"""

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from libs import constants
from services.review_bot.config import ReviewBotConfig
from services.review_bot.core import KnowledgeGraphBuilder


def main():
    """Main function to demonstrate knowledge graph building."""
    
    print(f"🚀 Building knowledge graph for repository: {constants.REPO_OWNER}/{constants.REPO_NAME}")
    print("📥 Will clone from GitHub and process source files")
    
    # Initialize knowledge graph builder
    neo4j_config = ReviewBotConfig.get_neo4j_config()
    builder = KnowledgeGraphBuilder(
        neo4j_uri=neo4j_config["uri"],
        neo4j_user=neo4j_config["user"],
        neo4j_password=neo4j_config["password"],
        use_temp_dir=False  # Use local directory for testing (no cleanup)
    )
    
    try:
        # Build the knowledge graph
        result = builder.build_knowledge_graph()
        
        if result['status'] == 'success':
            print("\n✅ Knowledge graph built successfully!")
            print("📊 Summary:")
            print(f"   Files processed: {result['files_successful']}/{result['files_discovered']}")
            print(f"   Total entities: {result['total_entities']}")
            print(f"   Total relationships: {result['total_relationships']}")
            print(f"   Duration: {result['duration_seconds']:.2f} seconds")
            
            print("\n💡 Next steps:")
            print("   1. Open Neo4j browser at http://localhost:7474")
            print("   2. Run Cypher queries to explore the knowledge graph")
            print("   3. Use the graph for code analysis and review bot features")
            
        else:
            print("\n❌ Knowledge graph build failed!")
            print(f"Error: {result['error']}")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Build interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()