#!/usr/bin/env python3
"""
Code Graph Example Usage

This script demonstrates how to use the code graph functionality
to analyze a codebase and extract insights.
"""

import sys
import os
sys.path.append('.')

from services.codegraph_service.graph_builder import CodeGraphBuilder
import json

def analyze_codebase(directory_path: str):
    """Analyze a codebase and generate insights."""
    
    print(f"🔍 Analyzing codebase: {directory_path}")
    print("=" * 60)
    
    # Initialize the graph builder
    builder = CodeGraphBuilder()
    
    try:
        # Index the directory
        print("📊 Indexing files...")
        stats = builder.index_directory(directory_path)
        
        print(f"✅ Indexing complete!")
        print(f"   Files processed: {stats['processed_files']}")
        print(f"   Nodes created: {stats['total_nodes']}")
        print(f"   Relationships: {stats['total_relationships']}")
        print(f"   Errors: {stats['error_files']}")
        
        if stats['errors']:
            print("⚠️  Errors encountered:")
            for error in stats['errors'][:5]:  # Show first 5 errors
                print(f"   - {error['file']}: {error['error']}")
        
        # Get comprehensive statistics
        print("\n📈 Codebase Statistics:")
        graph_stats = builder.get_graph_stats()
        
        # File statistics
        file_stats = graph_stats['files']
        print(f"📁 Files: {file_stats['total_files']} total, "
              f"{file_stats['parsed_files']} parsed, "
              f"{file_stats['error_files']} errors")
        
        # Node statistics
        print("🏗️  Code Elements:")
        for stat in graph_stats['nodes']:
            print(f"   - {stat['node_type'].capitalize()}: {stat['count']}")
        
        # Relationship statistics
        if graph_stats['relationships']:
            print("🔗 Relationships:")
            for stat in graph_stats['relationships']:
                print(f"   - {stat['relationship_type'].capitalize()}: {stat['count']}")
        
        # Find the most complex classes (most relationships)
        print("\n🏗️  Complex Classes:")
        classes = builder.search_nodes("", "class")
        class_complexity = []
        
        for cls in classes[:10]:  # Analyze first 10 classes
            relationships = builder.get_node_relationships(cls['id'])
            total_rels = len(relationships['outgoing']) + len(relationships['incoming'])
            class_complexity.append((cls['name'], cls['file_path'], total_rels))
        
        # Sort by complexity
        class_complexity.sort(key=lambda x: x[2], reverse=True)
        
        for name, file_path, rel_count in class_complexity[:5]:
            print(f"   - {name} ({file_path}): {rel_count} relationships")
        
        # Analyze import patterns
        print("\n📦 Import Analysis:")
        imports = builder.get_import_dependencies()
        
        # Group imports by importing file
        import_graph = {}
        for imp in imports:
            file = imp['importing_file']
            if file not in import_graph:
                import_graph[file] = []
            import_graph[file].append(imp['imported_name'])
        
        # Find files with most imports
        import_counts = [(file, len(imports)) for file, imports in import_graph.items()]
        import_counts.sort(key=lambda x: x[1], reverse=True)
        
        print("   Most import-heavy files:")
        for file, count in import_counts[:5]:
            print(f"   - {file}: {count} imports")
        
        # Analyze function distribution
        print("\n⚙️  Function Analysis:")
        functions = builder.search_nodes("", "function")
        
        # Group functions by file
        function_files = {}
        for func in functions:
            file = func['file_path']
            function_files[file] = function_files.get(file, 0) + 1
        
        # Find files with most functions
        function_counts = list(function_files.items())
        function_counts.sort(key=lambda x: x[1], reverse=True)
        
        print("   Function distribution:")
        for file, count in function_counts[:5]:
            print(f"   - {file}: {count} functions")
        
        # Search for common patterns
        print("\n🔍 Pattern Analysis:")
        
        # Find test files
        test_functions = [f for f in functions if 'test' in f['name'].lower() or 'spec' in f['name'].lower()]
        print(f"   Test functions found: {len(test_functions)}")
        
        # Find utility functions
        util_functions = [f for f in functions if any(word in f['name'].lower() 
                         for word in ['util', 'helper', 'common', 'shared'])]
        print(f"   Utility functions found: {len(util_functions)}")
        
        # Find async functions
        async_functions = [f for f in functions if f.get('metadata', {}).get('async', False) or 
                          'async' in (f.get('signature', '') or '')]
        print(f"   Async functions found: {len(async_functions)}")
        
        # Generate recommendations
        print("\n💡 Recommendations:")
        
        if stats['total_nodes'] < 50:
            print("   - Small codebase: Consider adding more comprehensive documentation")
        elif stats['total_nodes'] > 1000:
            print("   - Large codebase: Consider modularization and dependency management")
        
        if stats['total_relationships'] / max(stats['total_nodes'], 1) < 0.1:
            print("   - Low relationship density: Consider improving code connectivity analysis")
        
        if len(test_functions) / max(len(functions), 1) < 0.2:
            print("   - Low test coverage indicators: Consider adding more tests")
        
        error_rate = stats['error_files'] / max(stats['processed_files'] + stats['error_files'], 1)
        if error_rate > 0.1:
            print(f"   - High error rate ({error_rate:.1%}): Check parsing issues")
        
        # Export summary
        summary = {
            'indexing_stats': stats,
            'graph_stats': graph_stats,
            'complex_classes': class_complexity[:5],
            'import_heavy_files': import_counts[:5],
            'function_distribution': function_counts[:5],
            'pattern_analysis': {
                'test_functions': len(test_functions),
                'utility_functions': len(util_functions),
                'async_functions': len(async_functions)
            }
        }
        
        # Save summary to file
        with open('codegraph_analysis.json', 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"\n📄 Analysis summary saved to: codegraph_analysis.json")
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        builder.close()

def main():
    """Main entry point."""
    if len(sys.argv) != 2:
        print("Usage: python codegraph_example.py <directory_path>")
        print("\nExample:")
        print("  python codegraph_example.py /path/to/your/project/src")
        print("  python codegraph_example.py .")
        sys.exit(1)
    
    directory_path = sys.argv[1]
    
    if not os.path.exists(directory_path):
        print(f"❌ Directory does not exist: {directory_path}")
        sys.exit(1)
    
    analyze_codebase(directory_path)

if __name__ == "__main__":
    main()