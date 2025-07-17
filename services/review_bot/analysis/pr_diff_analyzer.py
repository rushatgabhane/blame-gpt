"""
PR Diff Analyzer - Analyzes git diffs from pull requests and builds a mini knowledge graph.
This module fetches PR diffs, parses changes, and creates a focused KG of modifications.
"""

import re
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from libs.github import repo
from libs import constants
from ..core.entity_extraction import EntityExtractor
from ..core.relationship_builder import RelationshipBuilder


class ChangeType(Enum):
    """Types of changes in a diff."""
    ADDED = "added"
    MODIFIED = "modified"
    DELETED = "deleted"


@dataclass
class FileChange:
    """Represents a change to a file in the PR."""
    file_path: str
    change_type: ChangeType
    additions: int
    deletions: int
    patch: Optional[str]
    old_content: Optional[str] = None
    new_content: Optional[str] = None


@dataclass
class FunctionChange:
    """Represents a change to a function."""
    name: str
    file_path: str
    change_type: ChangeType
    old_signature: Optional[str] = None
    new_signature: Optional[str] = None
    old_lines: Optional[Tuple[int, int]] = None
    new_lines: Optional[Tuple[int, int]] = None


class PRDiffAnalyzer:
    """Analyzes PR diffs and builds mini knowledge graphs of changes."""
    
    def __init__(self, repo_path: Optional[Path] = None):
        """
        Initialize the PR diff analyzer.
        
        Args:
            repo_path: Path to the local repository (optional, will clone if not provided)
        """
        self.repo_path = repo_path
        self.entity_extractor = EntityExtractor()
        self.relationship_builder = None
        self.file_changes: List[FileChange] = []
        self.function_changes: List[FunctionChange] = []
        
    def analyze_pr(self, pr_number: int) -> Dict[str, Any]:
        """
        Analyze a pull request and build a mini knowledge graph.
        
        Args:
            pr_number: GitHub PR number
            
        Returns:
            Dictionary containing the mini KG and analysis results
        """
        print(f"🔍 Analyzing PR #{pr_number}")
        
        # Step 1: Fetch PR diff and files
        pr_files = self._fetch_pr_files(pr_number)
        
        # Step 2: Parse file changes
        self.file_changes = self._parse_file_changes(pr_files)
        
        # Step 3: Extract entities from changed files
        entities_before = {}
        entities_after = {}
        
        for file_change in self.file_changes:
            if file_change.change_type != ChangeType.DELETED:
                # Analyze new/modified files
                entities_after[file_change.file_path] = self._extract_entities_from_content(
                    file_change.new_content,
                    file_change.file_path
                )
            
            if file_change.change_type != ChangeType.ADDED:
                # Analyze old version of modified/deleted files
                entities_before[file_change.file_path] = self._extract_entities_from_content(
                    file_change.old_content,
                    file_change.file_path
                )
        
        # Step 4: Compare entities to find changes
        self.function_changes = self._compare_entities(entities_before, entities_after)
        
        # Step 5: Build mini KG structure
        mini_kg = self._build_mini_kg(entities_after, self.file_changes, self.function_changes)
        
        # Step 6: Generate summary
        summary = self._generate_summary()
        
        return {
            "pr_number": pr_number,
            "summary": summary,
            "file_changes": [self._file_change_to_dict(fc) for fc in self.file_changes],
            "function_changes": [self._function_change_to_dict(fc) for fc in self.function_changes],
            "mini_kg": mini_kg,
            "entities_before": entities_before,
            "entities_after": entities_after
        }
    
    def _fetch_pr_files(self, pr_number: int) -> List[Dict[str, Any]]:
        """
        Fetch PR files and their diffs from GitHub.
        
        Args:
            pr_number: PR number
            
        Returns:
            List of file information with diffs
        """
        print(f"   📥 Fetching PR files from GitHub...")
        
        try:
            # Get the pull request
            pr = repo.get_pull(pr_number)
            
            # Get list of changed files
            files_data = []
            for file in pr.get_files():
                file_info = {
                    'filename': file.filename,
                    'status': file.status,
                    'additions': file.additions,
                    'deletions': file.deletions,
                    'changes': file.changes,
                    'patch': file.patch if hasattr(file, 'patch') else None,
                    'contents_url': file.contents_url,
                    'blob_url': file.blob_url,
                    'raw_url': file.raw_url,
                    'sha': file.sha
                }
                
                # Get file contents before and after (for modified files)
                if file.status == 'modified':
                    try:
                        # Get content at base commit
                        base_content = repo.get_contents(file.filename, ref=pr.base.sha)
                        file_info['old_content'] = base_content.decoded_content.decode('utf-8')
                    except Exception:
                        file_info['old_content'] = None
                    
                    try:
                        # Get content at head commit
                        head_content = repo.get_contents(file.filename, ref=pr.head.sha)
                        file_info['new_content'] = head_content.decoded_content.decode('utf-8')
                    except Exception:
                        file_info['new_content'] = None
                
                elif file.status == 'added':
                    file_info['old_content'] = None
                    try:
                        # Get content at head commit
                        head_content = repo.get_contents(file.filename, ref=pr.head.sha)
                        file_info['new_content'] = head_content.decoded_content.decode('utf-8')
                    except Exception:
                        file_info['new_content'] = None
                
                elif file.status == 'removed':
                    try:
                        # Get content at base commit
                        base_content = repo.get_contents(file.filename, ref=pr.base.sha)
                        file_info['old_content'] = base_content.decoded_content.decode('utf-8')
                    except Exception:
                        file_info['old_content'] = None
                    file_info['new_content'] = None
                
                files_data.append(file_info)
            
            print(f"   ✅ Fetched {len(files_data)} changed files")
            return files_data
            
        except Exception as e:
            print(f"   ❌ Error fetching PR files: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    
    def _parse_file_changes(self, pr_files: List[Dict[str, Any]]) -> List[FileChange]:
        """
        Parse PR files into FileChange objects.
        
        Args:
            pr_files: List of file information from GitHub
            
        Returns:
            List of FileChange objects
        """
        file_changes = []
        
        for file_info in pr_files:
            # Skip non-JS/TS files
            filename = file_info.get('filename', '')
            if not any(filename.endswith(ext) for ext in ['.js', '.jsx', '.ts', '.tsx']):
                continue
            
            # Determine change type
            status = file_info.get('status', 'modified')
            if status == 'added':
                change_type = ChangeType.ADDED
            elif status == 'removed':
                change_type = ChangeType.DELETED
            else:
                change_type = ChangeType.MODIFIED
            
            file_change = FileChange(
                file_path=filename,
                change_type=change_type,
                additions=file_info.get('additions', 0),
                deletions=file_info.get('deletions', 0),
                patch=file_info.get('patch'),
                old_content=file_info.get('old_content'),
                new_content=file_info.get('new_content')
            )
            
            file_changes.append(file_change)
        
        return file_changes
    
    def _extract_entities_from_content(self, content: Optional[str], file_path: str) -> Dict[str, Any]:
        """
        Extract entities from file content.
        
        Args:
            content: File content
            file_path: Path to the file
            
        Returns:
            Entity extraction results
        """
        if not content:
            return {
                "file_path": file_path,
                "success": False,
                "error": "No content available",
                "functions": [],
                "classes": [],
                "imports": [],
                "exports": [],
                "function_calls": [],
                "variables": [],
                "total_entities": 0
            }
        
        # Write content to temporary file for tree-sitter parsing
        with tempfile.NamedTemporaryFile(mode='w', suffix=Path(file_path).suffix, delete=False) as tmp:
            tmp.write(content)
            tmp_path = Path(tmp.name)
        
        try:
            # Use entity extractor
            result = self.entity_extractor.analyze_file(tmp_path)
            result["file_path"] = file_path  # Use original file path
            return result
        finally:
            # Clean up temp file
            tmp_path.unlink()
    
    def _compare_entities(
        self,
        entities_before: Dict[str, Dict[str, Any]],
        entities_after: Dict[str, Dict[str, Any]]
    ) -> List[FunctionChange]:
        """
        Compare entities before and after to identify function changes.
        
        Args:
            entities_before: Entities from files before changes
            entities_after: Entities from files after changes
            
        Returns:
            List of function changes
        """
        function_changes = []
        
        # Check all files that were analyzed
        all_files = set(entities_before.keys()) | set(entities_after.keys())
        
        for file_path in all_files:
            before = entities_before.get(file_path, {"functions": []})
            after = entities_after.get(file_path, {"functions": []})
            
            # Create function maps
            before_funcs = {f["name"]: f for f in before.get("functions", [])}
            after_funcs = {f["name"]: f for f in after.get("functions", [])}
            
            # Find added functions
            for name, func in after_funcs.items():
                if name not in before_funcs:
                    function_changes.append(FunctionChange(
                        name=name,
                        file_path=file_path,
                        change_type=ChangeType.ADDED,
                        new_lines=(func["start_line"], func["end_line"])
                    ))
            
            # Find deleted functions
            for name, func in before_funcs.items():
                if name not in after_funcs:
                    function_changes.append(FunctionChange(
                        name=name,
                        file_path=file_path,
                        change_type=ChangeType.DELETED,
                        old_lines=(func["start_line"], func["end_line"])
                    ))
            
            # Find modified functions
            for name in set(before_funcs.keys()) & set(after_funcs.keys()):
                before_func = before_funcs[name]
                after_func = after_funcs[name]
                
                # Check if function was modified (simple check based on lines)
                if (before_func["start_line"] != after_func["start_line"] or 
                    before_func["end_line"] != after_func["end_line"]):
                    function_changes.append(FunctionChange(
                        name=name,
                        file_path=file_path,
                        change_type=ChangeType.MODIFIED,
                        old_lines=(before_func["start_line"], before_func["end_line"]),
                        new_lines=(after_func["start_line"], after_func["end_line"])
                    ))
        
        return function_changes
    
    def _build_mini_kg(
        self,
        entities: Dict[str, Dict[str, Any]],
        file_changes: List[FileChange],
        function_changes: List[FunctionChange]
    ) -> Dict[str, Any]:
        """
        Build a mini knowledge graph structure from the changes.
        
        Args:
            entities: Current entities after changes
            file_changes: List of file changes
            function_changes: List of function changes
            
        Returns:
            Mini knowledge graph structure
        """
        mini_kg = {
            "nodes": {
                "files": [],
                "functions": [],
                "classes": [],
                "imports": []
            },
            "relationships": {
                "contains": [],
                "imports": [],
                "calls": [],
                "modifies": []
            },
            "changes": {
                "added_functions": [],
                "modified_functions": [],
                "deleted_functions": [],
                "added_files": [],
                "modified_files": [],
                "deleted_files": []
            }
        }
        
        # Add file nodes
        for file_change in file_changes:
            file_node = {
                "path": file_change.file_path,
                "change_type": file_change.change_type.value,
                "additions": file_change.additions,
                "deletions": file_change.deletions
            }
            mini_kg["nodes"]["files"].append(file_node)
            
            # Track file changes
            if file_change.change_type == ChangeType.ADDED:
                mini_kg["changes"]["added_files"].append(file_change.file_path)
            elif file_change.change_type == ChangeType.MODIFIED:
                mini_kg["changes"]["modified_files"].append(file_change.file_path)
            elif file_change.change_type == ChangeType.DELETED:
                mini_kg["changes"]["deleted_files"].append(file_change.file_path)
        
        # Add entity nodes from current state
        for file_path, entity_data in entities.items():
            if not entity_data.get("success", False):
                continue
            
            # Add functions
            for func in entity_data.get("functions", []):
                func_node = {
                    "name": func["name"],
                    "file_path": file_path,
                    "start_line": func["start_line"],
                    "end_line": func["end_line"],
                    "type": func["type"]
                }
                mini_kg["nodes"]["functions"].append(func_node)
                
                # Add contains relationship
                mini_kg["relationships"]["contains"].append({
                    "source": file_path,
                    "target": func["name"],
                    "type": "file_contains_function"
                })
            
            # Add classes
            for cls in entity_data.get("classes", []):
                cls_node = {
                    "name": cls["name"],
                    "file_path": file_path,
                    "start_line": cls["start_line"],
                    "end_line": cls["end_line"]
                }
                mini_kg["nodes"]["classes"].append(cls_node)
                
                # Add contains relationship
                mini_kg["relationships"]["contains"].append({
                    "source": file_path,
                    "target": cls["name"],
                    "type": "file_contains_class"
                })
            
            # Add imports
            for imp in entity_data.get("imports", []):
                imp_node = {
                    "module": imp["module"],
                    "file_path": file_path,
                    "alias_map": imp["alias_map"],
                    "line": imp["line"]
                }
                mini_kg["nodes"]["imports"].append(imp_node)
                
                # Add import relationship
                mini_kg["relationships"]["imports"].append({
                    "source": file_path,
                    "target": imp["module"],
                    "type": "file_imports_module"
                })
            
            # Add function calls as relationships
            for call in entity_data.get("function_calls", []):
                mini_kg["relationships"]["calls"].append({
                    "source": file_path,
                    "target": call["target"],
                    "line": call["line"],
                    "call_type": call["call_type"]
                })
        
        # Track function changes
        for func_change in function_changes:
            change_info = {
                "name": func_change.name,
                "file_path": func_change.file_path,
                "change_type": func_change.change_type.value
            }
            
            if func_change.change_type == ChangeType.ADDED:
                mini_kg["changes"]["added_functions"].append(change_info)
            elif func_change.change_type == ChangeType.MODIFIED:
                mini_kg["changes"]["modified_functions"].append(change_info)
            elif func_change.change_type == ChangeType.DELETED:
                mini_kg["changes"]["deleted_functions"].append(change_info)
        
        return mini_kg
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate a summary of the changes."""
        return {
            "total_files_changed": len(self.file_changes),
            "files_added": len([f for f in self.file_changes if f.change_type == ChangeType.ADDED]),
            "files_modified": len([f for f in self.file_changes if f.change_type == ChangeType.MODIFIED]),
            "files_deleted": len([f for f in self.file_changes if f.change_type == ChangeType.DELETED]),
            "total_functions_changed": len(self.function_changes),
            "functions_added": len([f for f in self.function_changes if f.change_type == ChangeType.ADDED]),
            "functions_modified": len([f for f in self.function_changes if f.change_type == ChangeType.MODIFIED]),
            "functions_deleted": len([f for f in self.function_changes if f.change_type == ChangeType.DELETED]),
            "total_additions": sum(f.additions for f in self.file_changes),
            "total_deletions": sum(f.deletions for f in self.file_changes)
        }
    
    def _file_change_to_dict(self, file_change: FileChange) -> Dict[str, Any]:
        """Convert FileChange to dictionary."""
        return {
            "file_path": file_change.file_path,
            "change_type": file_change.change_type.value,
            "additions": file_change.additions,
            "deletions": file_change.deletions,
            "has_patch": file_change.patch is not None
        }
    
    def _function_change_to_dict(self, func_change: FunctionChange) -> Dict[str, Any]:
        """Convert FunctionChange to dictionary."""
        return {
            "name": func_change.name,
            "file_path": func_change.file_path,
            "change_type": func_change.change_type.value,
            "old_lines": func_change.old_lines,
            "new_lines": func_change.new_lines
        }