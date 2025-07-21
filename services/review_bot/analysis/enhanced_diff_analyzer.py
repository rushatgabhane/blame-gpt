"""
Enhanced Diff Analyzer - Parses git diffs at line level to find actually changed functions.
This analyzer looks at the actual diff lines to determine which functions contain changes.
"""

import re
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass

from .pr_diff_analyzer import PRDiffAnalyzer, ChangeType, FunctionChange
from ..core.entity_extraction import EntityExtractor


@dataclass
class DiffHunk:
    """Represents a hunk (change block) in a git diff."""
    old_start: int
    old_count: int
    new_start: int
    new_count: int
    changes: List[str]  # List of diff lines (+ - or context)


@dataclass
class LineChange:
    """Represents a changed line in a file."""
    line_number: int
    change_type: str  # '+', '-', or ' ' (context)
    content: str


class EnhancedDiffAnalyzer(PRDiffAnalyzer):
    """Enhanced analyzer that parses actual diff lines to find changed functions."""
    
    def __init__(self, repo_path: Optional[Path] = None):
        """Initialize enhanced diff analyzer."""
        super().__init__(repo_path)
        self.entity_extractor = EntityExtractor()
    
    def analyze_pr_with_line_diffs(self, pr_number: int) -> Dict[str, Any]:
        """
        Analyze PR with actual line-level diff parsing.
        
        Args:
            pr_number: GitHub PR number
            
        Returns:
            Enhanced analysis with line-level function change detection
        """
        print(f"🔍 Enhanced Analysis: PR #{pr_number} with line-level diff parsing")
        
        # Get basic PR analysis first
        basic_analysis = self.analyze_pr(pr_number)
        
        # Now enhance with line-level diff analysis
        enhanced_function_changes = []
        
        for file_change in self.file_changes:
            if file_change.patch and file_change.new_content:
                # Parse the diff patch to get changed lines
                changed_lines = self._parse_diff_patch(file_change.patch)
                
                # Extract functions from the current file content
                file_entities = self._extract_entities_from_content(
                    file_change.new_content, 
                    file_change.file_path
                )
                
                # Find which functions contain the changed lines
                functions_with_changes = self._find_functions_containing_changes(
                    file_entities.get("functions", []), 
                    changed_lines,
                    file_change.file_path
                )
                
                enhanced_function_changes.extend(functions_with_changes)
        
        # Update the analysis with enhanced function changes
        basic_analysis["enhanced_function_changes"] = [
            self._enhanced_function_change_to_dict(fc) for fc in enhanced_function_changes
        ]
        
        # Update summary
        basic_analysis["summary"]["enhanced_functions_changed"] = len(enhanced_function_changes)
        
        print(f"✅ Enhanced analysis complete!")
        print(f"   Original function changes: {len(basic_analysis['function_changes'])}")
        print(f"   Enhanced function changes: {len(enhanced_function_changes)}")
        
        return basic_analysis
    
    def _parse_diff_patch(self, patch: str) -> List[LineChange]:
        """
        Parse a git diff patch to extract changed lines.
        
        Args:
            patch: Git diff patch string
            
        Returns:
            List of line changes with line numbers
        """
        changed_lines = []
        current_new_line = 0
        
        # Split patch into lines
        lines = patch.split('\n')
        
        for line in lines:
            # Parse hunk headers like @@ -old_start,old_count +new_start,new_count @@
            hunk_match = re.match(r'^@@\s+-(\d+),?(\d*)\s+\+(\d+),?(\d*)\s+@@', line)
            if hunk_match:
                new_start = int(hunk_match.group(3))
                current_new_line = new_start
                continue
            
            # Process diff lines
            if line.startswith('+') and not line.startswith('+++'):
                # Added line
                changed_lines.append(LineChange(
                    line_number=current_new_line,
                    change_type='+',
                    content=line[1:]  # Remove the + prefix
                ))
                current_new_line += 1
            elif line.startswith('-') and not line.startswith('---'):
                # Deleted line (don't increment new line number)
                changed_lines.append(LineChange(
                    line_number=current_new_line,
                    change_type='-',
                    content=line[1:]  # Remove the - prefix
                ))
            elif line.startswith(' ') or (not line.startswith('+') and not line.startswith('-')):
                # Context line or regular content
                current_new_line += 1
        
        return changed_lines
    
    def _find_functions_containing_changes(
        self, 
        functions: List[Dict[str, Any]], 
        changed_lines: List[LineChange],
        file_path: str
    ) -> List[FunctionChange]:
        """
        Find which functions contain the changed lines.
        
        Args:
            functions: List of functions from entity extraction
            changed_lines: List of changed lines from diff
            file_path: Path to the file
            
        Returns:
            List of functions that contain changes
        """
        functions_with_changes = []
        
        # Get all changed line numbers (additions and modifications)
        changed_line_numbers = set()
        for change in changed_lines:
            if change.change_type in ['+', '-']:
                changed_line_numbers.add(change.line_number)
        
        print(f"   📍 File: {file_path}")
        print(f"   📍 Changed lines: {sorted(changed_line_numbers)}")
        
        # Check each function to see if it contains any changed lines
        for func in functions:
            start_line = func.get("start_line")
            end_line = func.get("end_line")
            
            if start_line is None or end_line is None:
                continue
            
            # Check if any changed lines fall within this function's range
            function_changed_lines = [
                line_num for line_num in changed_line_numbers 
                if start_line <= line_num <= end_line
            ]
            
            if function_changed_lines:
                print(f"   ✅ Function '{func['name']}' (lines {start_line}-{end_line}) contains changes at lines: {function_changed_lines}")
                
                functions_with_changes.append(FunctionChange(
                    name=func["name"],
                    file_path=file_path,
                    change_type=ChangeType.MODIFIED,
                    new_lines=(start_line, end_line),
                    old_lines=(start_line, end_line)  # For now, assume same lines
                ))
            else:
                print(f"   ⚪ Function '{func['name']}' (lines {start_line}-{end_line}) - no changes")
        
        return functions_with_changes
    
    def _enhanced_function_change_to_dict(self, fc: FunctionChange) -> Dict[str, Any]:
        """Convert enhanced function change to dictionary."""
        return {
            "name": fc.name,
            "file_path": fc.file_path,
            "change_type": fc.change_type.value,
            "old_signature": fc.old_signature,
            "new_signature": fc.new_signature,
            "old_lines": fc.old_lines,
            "new_lines": fc.new_lines,
            "detection_method": "line_level_diff"
        }


def test_enhanced_analyzer():
    """Test the enhanced analyzer with PR 65748."""
    print("🧪 Testing Enhanced Diff Analyzer")
    print("=" * 50)
    
    # Initialize analyzer
    analyzer = EnhancedDiffAnalyzer()
    
    # Analyze PR 65748
    results = analyzer.analyze_pr_with_line_diffs(65748)
    
    # Print results
    print("\n📊 Enhanced Analysis Results:")
    print("=" * 30)
    
    print(f"Original function changes: {len(results['function_changes'])}")
    print(f"Enhanced function changes: {len(results.get('enhanced_function_changes', []))}")
    
    if results.get('enhanced_function_changes'):
        print("\n🎯 Functions with actual changes:")
        for fc in results['enhanced_function_changes']:
            print(f"   - {fc['name']} in {fc['file_path']} (lines {fc['new_lines']})")
    else:
        print("\n❌ No functions with changes detected")
    
    return results


if __name__ == "__main__":
    test_enhanced_analyzer()