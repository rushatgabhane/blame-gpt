"""
Knowledge graph builder - orchestrates the entire process of building a knowledge graph from a codebase.
Uses the latest commit state instead of a baseline commit.
"""

import os
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

from .entity_extraction import EntityExtractor
from .relationship_builder import RelationshipBuilder
from libs.neo4j_client import Neo4jClient
from libs import constants
from libs.github import repo as github_repo


class KnowledgeGraphBuilder:
    def __init__(
        self,
        neo4j_uri: str = "bolt://localhost:7687",
        neo4j_user: str = "neo4j", 
        neo4j_password: str = "password",
        use_temp_dir: bool = False  # Changed default to False for testing
    ):
        """
        Initialize the knowledge graph builder.
        
        Args:
            neo4j_uri: Neo4j connection URI
            neo4j_user: Neo4j username
            neo4j_password: Neo4j password
            use_temp_dir: Whether to use temporary directory for cloning
        """
        self.use_temp_dir = use_temp_dir
        self.repo_path = None
        self.src_dir = None
        self.temp_dir = None
        
        # Initialize components
        self.entity_extractor = EntityExtractor()
        self.relationship_builder = None  # Will be set after repo is cloned
        self.neo4j_client = Neo4jClient(neo4j_uri, neo4j_user, neo4j_password)
        
        # Results storage
        self.file_analyses = []
        self.all_relationships = {}
        
    def clone_repository(self) -> bool:
        """
        Clone the target repository from GitHub.
        
        Returns:
            True if successful, False otherwise
        """
        print("📥 Cloning repository from GitHub...")
        
        try:
            if self.use_temp_dir:
                # Create temporary directory
                self.temp_dir = tempfile.mkdtemp(prefix="review_bot_")
                self.repo_path = Path(self.temp_dir) / f"{constants.REPO_NAME}"
                print(f"   Using temporary directory: {self.temp_dir}")
            else:
                # Use local directory (for testing and development)
                # Find project root (go up to find the directory containing libs/)
                current_dir = Path(__file__).parent
                while current_dir.parent != current_dir:
                    if (current_dir / "libs").exists():
                        project_root = current_dir
                        break
                    current_dir = current_dir.parent
                else:
                    # Fallback to current working directory
                    project_root = Path.cwd()
                
                local_dir = project_root / "local"
                local_dir.mkdir(exist_ok=True)  # Create local dir if it doesn't exist
                self.repo_path = local_dir / f"{constants.REPO_NAME}"
                print(f"   Using local directory: {self.repo_path}")
                
            # Check if repository already exists locally
            if self.repo_path.exists():
                print(f"   📁 Repository already exists at {self.repo_path}")
                print(f"   ⏭️  Skipping clone, using existing repository")
                print(f"   💡 To update: delete {self.repo_path} and run again")
            else:
                # Clone the repository
                clone_url = f"https://github.com/{constants.REPO_OWNER}/{constants.REPO_NAME}.git"
                print(f"   📥 Cloning from: {clone_url}")
                
                result = subprocess.run([
                    'git', 'clone', '--depth', '1',  # Shallow clone for efficiency
                    clone_url, str(self.repo_path)
                ], capture_output=True, text=True, check=True)
                
                print(f"   ✅ Repository cloned successfully")
            
            self.src_dir = self.repo_path / "src"
            
            # Initialize relationship builder now that we have repo path
            self.relationship_builder = RelationshipBuilder(self.repo_path)
            
            print(f"   ✅ Repository cloned to: {self.repo_path}")
            print(f"   📁 Source directory: {self.src_dir}")
            
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"   ❌ Git clone failed: {e.stderr}")
            return False
        except Exception as e:
            print(f"   ❌ Clone error: {e}")
            return False
    
    def cleanup_repository(self):
        """Clean up temporary directory if used. Keep local directory for testing."""
        if self.temp_dir and self.use_temp_dir:
            try:
                shutil.rmtree(self.temp_dir)
                print(f"   🧹 Cleaned up temporary directory: {self.temp_dir}")
            except Exception as e:
                print(f"   ⚠️ Failed to cleanup {self.temp_dir}: {e}")
        else:
            print(f"   💾 Keeping repository in local directory: {self.repo_path}")
            print(f"   💡 Repository will be reused on next run for faster processing")

    def run_git_command(self, cmd: List[str]) -> Optional[str]:
        """Run a git command and return the output."""
        try:
            result = subprocess.run(
                cmd, 
                cwd=self.repo_path, 
                capture_output=True, 
                text=True, 
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            print(f"Git command failed: {' '.join(cmd)}")
            print(f"Error: {e.stderr}")
            return None

    def get_repository_state(self) -> Dict[str, Any]:
        """
        Get current repository state (using latest commit instead of baseline).
        
        Returns:
            Dictionary with repository information
        """
        print("📍 Getting current repository state...")
        
        # Get current commit info
        current_hash = self.run_git_command(['git', 'rev-parse', 'HEAD'])
        current_branch = self.run_git_command(['git', 'branch', '--show-current'])
        
        if not current_hash:
            raise Exception("Could not get current commit hash")
        
        commit_info = self.run_git_command(['git', 'log', '--oneline', '-1'])
        commit_date = self.run_git_command(['git', 'log', '--format=%cd', '--date=short', '-1'])
        
        print(f"   Commit Hash: {current_hash}")
        print(f"   Branch: {current_branch if current_branch else 'DETACHED HEAD'}")
        print(f"   Commit: {commit_info}")
        print(f"   Date: {commit_date}")
        
        return {
            'hash': current_hash,
            'branch': current_branch,
            'commit_info': commit_info,
            'commit_date': commit_date,
            'timestamp': datetime.now().isoformat()
        }

    def discover_files(self) -> List[Path]:
        """
        Discover JavaScript/TypeScript files in the src/ directory.
        
        Returns:
            List of file paths
        """
        print("🔍 Discovering JavaScript/TypeScript files...")
        
        if not self.src_dir.exists():
            raise Exception(f"Source directory not found: {self.src_dir}")
        
        # File patterns to look for
        patterns = ['**/*.js', '**/*.ts', '**/*.tsx', '**/*.jsx']
        
        all_files = []
        for pattern in patterns:
            files = list(self.src_dir.glob(pattern))
            all_files.extend(files)
        
        # Filter out test files, build files, etc.
        exclude_patterns = ['test', 'spec', '__tests__', 'node_modules', '.git', 'dist', 'build']
        
        filtered_files = []
        for file_path in all_files:
            file_str = str(file_path)
            if not any(pattern in file_str for pattern in exclude_patterns):
                filtered_files.append(file_path)
        
        print(f"   Found {len(all_files)} total files")
        print(f"   Filtered to {len(filtered_files)} relevant files")
        
        # Group by extension
        by_extension = {}
        for file_path in filtered_files:
            ext = file_path.suffix
            by_extension[ext] = by_extension.get(ext, 0) + 1
        
        for ext, count in by_extension.items():
            print(f"   {ext}: {count} files")
        
        return filtered_files

    def analyze_files(self, files: List[Path]) -> List[Dict[str, Any]]:
        """
        Analyze all discovered files for entities and relationships.
        
        Args:
            files: List of file paths to analyze
            
        Returns:
            List of analysis results
        """
        print(f"🔄 Analyzing {len(files)} files...")
        
        analyses = []
        failed_files = []
        
        for i, file_path in enumerate(files, 1):
            file_name = file_path.name
            print(f"   Processing {i:2d}/{len(files)}: {file_name}")
            
            try:
                result = self.entity_extractor.analyze_file(file_path)
                analyses.append(result)
                
                if result['success']:
                    entities = result['total_entities']
                    calls = len(result['function_calls'])
                    print(f"      ✅ {entities} entities, {calls} function calls")
                else:
                    print(f"      ❌ Analysis failed: {result.get('error', 'Unknown error')}")
                    failed_files.append(file_path)
                    
            except Exception as e:
                print(f"      ❌ Exception: {str(e)[:50]}...")
                failed_files.append(file_path)
                # Add a failed result to maintain consistency
                analyses.append({
                    'file_path': str(file_path),
                    'success': False,
                    'error': str(e),
                    'total_entities': 0,
                    'functions': [],
                    'classes': [],
                    'variables': [],
                    'imports': [],
                    'exports': [],
                    'function_calls': []
                })
            
            # Progress update every 10 files
            if i % 10 == 0:
                successful = len([r for r in analyses if r['success']])
                print(f"   📊 Progress: {successful}/{i} files processed successfully")

        # Final statistics
        successful_files = [r for r in analyses if r['success']]
        print(f"\n📊 Processing Summary:")
        print(f"   ✅ Successful: {len(successful_files)} files")
        print(f"   ❌ Failed: {len(failed_files)} files")

        if failed_files:
            print(f"   ⚠️  Failed files: {', '.join(f.name for f in failed_files[:5])}")
            if len(failed_files) > 5:
                print(f"        ... and {len(failed_files) - 5} more")

        # Calculate totals
        total_entities = sum(r['total_entities'] for r in successful_files)
        total_functions = sum(len(r['functions']) for r in successful_files)
        total_classes = sum(len(r['classes']) for r in successful_files)
        total_variables = sum(len(r['variables']) for r in successful_files)
        total_imports = sum(len(r['imports']) for r in successful_files)
        total_exports = sum(len(r['exports']) for r in successful_files)
        total_function_calls = sum(len(r['function_calls']) for r in successful_files)

        print(f"\n📈 Entity Statistics:")
        print(f"   🏗️  Total entities: {total_entities}")
        print(f"   ⚙️  Functions: {total_functions}")
        print(f"   🏛️  Classes: {total_classes}")
        print(f"   📦 Variables: {total_variables}")
        print(f"   📥 Imports: {total_imports}")
        print(f"   📤 Exports: {total_exports}")
        print(f"   📞 Function calls: {total_function_calls}")

        return analyses

    def build_relationships(self, analyses: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Build all types of relationships from analysis results.
        
        Args:
            analyses: List of file analysis results
            
        Returns:
            Dictionary containing all relationship types
        """
        print("🔗 Building relationships...")
        
        successful_files = [r for r in analyses if r['success']]
        print(f"   Processing relationships for {len(successful_files)} successful files")
        
        relationships = self.relationship_builder.build_all_relationships(analyses)
        
        # Print relationship statistics
        print(f"\n📊 Relationship Statistics:")
        for rel_type, rel_list in relationships.items():
            print(f"   {rel_type}: {len(rel_list)}")
        
        return relationships

    def load_to_neo4j(self, analyses: List[Dict[str, Any]], relationships: Dict[str, List[Dict[str, Any]]]):
        """
        Load all data into Neo4j database.
        
        Args:
            analyses: List of file analysis results
            relationships: Dictionary of all relationship types
        """
        print("💾 Loading data to Neo4j...")
        
        # Connect to Neo4j
        success, message = self.neo4j_client.connect()
        if not success:
            raise Exception(f"Failed to connect to Neo4j: {message}")
        print(f"   ✅ {message}")
        
        try:
            # Initialize schema
            print("   📋 Initializing schema...")
            if not self.neo4j_client.init_schema():
                raise Exception("Failed to initialize Neo4j schema")
            
            # Load files
            print("   📁 Loading file nodes...")
            file_count = self.neo4j_client.load_files(analyses, self.repo_path)
            print(f"      ✅ {file_count} files loaded")
            
            # Load entities
            print("   🏗️  Loading entity nodes...")
            func_count, class_count, var_count = self.neo4j_client.load_entities(analyses)
            print(f"      ✅ {func_count} functions, {class_count} classes, {var_count} variables")
            
            # Load CONTAINS relationships
            print("   🔗 Loading CONTAINS relationships...")
            contains_count = self.neo4j_client.load_contains_relationships(analyses)
            print(f"      ✅ {contains_count} CONTAINS relationships")
            
            # Load import relationships
            print("   📥 Loading import relationships...")
            internal_imports, external_imports = self.neo4j_client.load_import_relationships(
                relationships['file_relationships']
            )
            print(f"      ✅ {internal_imports} internal, {external_imports} external imports")
            
            # Load function call relationships
            print("   📞 Loading function call relationships...")
            call_count = self.neo4j_client.load_function_call_relationships(
                relationships['function_call_relationships']
            )
            print(f"      ✅ {call_count} function call nodes")
            
            # Resolve same-file calls
            print("   🔀 Resolving same-file function calls...")
            if self.neo4j_client.resolve_same_file_calls():
                print("      ✅ Same-file INVOKES relationships created")
            
            # Load cross-file function call relationships
            print("   🌐 Loading cross-file function calls...")
            cross_file_count = self.neo4j_client.load_cross_file_call_relationships(
                relationships['cross_file_call_relationships']
            )
            print(f"      ✅ {cross_file_count} cross-file INVOKES relationships created")
            
            # Get final statistics
            stats = self.neo4j_client.get_stats()
            if stats:
                print(f"\n📊 Final Neo4j Statistics:")
                print(f"   Nodes: {stats['total_nodes']}")
                print(f"   Relationships: {stats['total_relationships']}")
                
                print(f"\n   Node types:")
                for node_type, count in stats['nodes'].items():
                    print(f"      {node_type}: {count}")
                
                print(f"\n   Relationship types:")
                for rel_type, count in stats['relationships'].items():
                    print(f"      {rel_type}: {count}")
            
        finally:
            self.neo4j_client.disconnect()
            print("   🔌 Neo4j connection closed")

    def build_knowledge_graph(self) -> Dict[str, Any]:
        """
        Main method to build the complete knowledge graph.
        
        Returns:
            Dictionary with build results and statistics
        """
        start_time = datetime.now()
        
        print("🚀 Starting Knowledge Graph Construction")
        print(f"🎯 Target Repository: {constants.REPO_OWNER}/{constants.REPO_NAME}")
        print("=" * 60)
        
        try:
            # Step 0: Clone repository from GitHub
            if not self.clone_repository():
                raise Exception("Failed to clone repository")
            
            # Step 1: Get repository state (latest commit)
            repo_state = self.get_repository_state()
            
            # Step 2: Discover files
            files = self.discover_files()
            
            # Step 3: Analyze files
            self.file_analyses = self.analyze_files(files)
            
            # Step 4: Build relationships
            self.all_relationships = self.build_relationships(self.file_analyses)
            
            # Step 5: Load to Neo4j
            self.load_to_neo4j(self.file_analyses, self.all_relationships)
            
            end_time = datetime.now()
            duration = end_time - start_time
            
            # Build summary
            successful_analyses = [a for a in self.file_analyses if a['success']]
            
            summary = {
                'status': 'success',
                'repository': f"{constants.REPO_OWNER}/{constants.REPO_NAME}",
                'repository_state': repo_state,
                'files_discovered': len(files),
                'files_analyzed': len(self.file_analyses),
                'files_successful': len(successful_analyses),
                'total_entities': sum(a['total_entities'] for a in successful_analyses),
                'total_relationships': sum(len(rels) for rels in self.all_relationships.values()),
                'duration_seconds': duration.total_seconds(),
                'completed_at': end_time.isoformat()
            }
            
            print(f"\n🎉 Knowledge Graph Construction Complete!")
            print(f"   Repository: {summary['repository']}")
            print(f"   Duration: {duration.total_seconds():.2f} seconds")
            print(f"   Files processed: {summary['files_successful']}/{summary['files_discovered']}")
            print(f"   Total entities: {summary['total_entities']}")
            print(f"   Total relationships: {summary['total_relationships']}")
            
            return summary
            
        except Exception as e:
            error_summary = {
                'status': 'error',
                'repository': f"{constants.REPO_OWNER}/{constants.REPO_NAME}",
                'error': str(e),
                'duration_seconds': (datetime.now() - start_time).total_seconds(),
                'failed_at': datetime.now().isoformat()
            }
            
            print(f"\n❌ Knowledge Graph Construction Failed!")
            print(f"   Error: {str(e)}")
            
            return error_summary
            
        finally:
            # Always cleanup temporary directory
            self.cleanup_repository()