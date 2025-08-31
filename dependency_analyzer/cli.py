"""
Command-line interface for the dependency analyzer.

WHAT IT DOES:
- Provides comprehensive command-line interface for all analyzer functionality
- Supports both basic project analysis and advanced diff-based PR analysis
- Offers flexible output formatting and integration options
- Enables automation through CI/CD pipelines and scripting

HOW IT WORKS:
1. **Argument Parsing**: Processes command-line arguments and options
2. **Mode Selection**: Determines whether to run full analysis or diff analysis
3. **Configuration**: Sets up analyzers with appropriate options and settings
4. **Execution**: Runs the selected analysis mode with proper error handling
5. **Output Generation**: Formats and exports results in requested formats
6. **Status Reporting**: Provides appropriate exit codes for automation

ANALYSIS MODES:

Full Project Analysis:
- Scans entire project for all dependency files
- Generates comprehensive reports with statistics
- Supports advanced features (conflicts, duplicates, categorization)
- Exports to multiple formats (CSV, JSON, HTML, Markdown)
- Example: `python -m dependency_analyzer --advanced --stats`

Diff Analysis Mode:
- Analyzes dependency changes in git diffs or PRs
- Detects added, removed, and updated dependencies
- Supports multiple diff sources (git, GitHub PR, files)
- Perfect for CI/CD and PR review automation
- Example: `python -m dependency_analyzer --diff --format json`

COMMAND OPTIONS:

Basic Options:
- `--format`: Export format selection (csv,json,html,md)
- `--output`: Output directory for generated reports
- `--name`: Custom project name for reports
- `--quiet/--verbose`: Output control for automation

Advanced Options:
- `--advanced`: Enable advanced analysis features
- `--find-conflicts`: Detect version conflicts
- `--find-duplicates`: Identify duplicate dependencies
- `--stats`: Show detailed statistics

Diff Options:
- `--diff`: Enable diff analysis mode
- `--base-ref/--head-ref`: Git references for comparison
- `--pr-url`: GitHub PR URL for direct PR analysis
- `--github-token`: Authentication for private repositories
- `--diff-file`: Analyze saved diff files

INTEGRATION FEATURES:

CI/CD Integration:
- Quiet mode for script automation
- JSON output for data processing
- Appropriate exit codes for pipeline decisions
- Error handling and logging

GitHub Actions:
- PR comment generation
- Security scanning alerts
- Dependency change notifications
- Automated report publishing

VS Code Integration:
- Task integration for on-demand analysis
- Output formatting for editor display
- File path handling for workspace navigation
- Extension command compatibility

USAGE EXAMPLES:
- Project audit: `python -m dependency_analyzer --advanced --stats`
- PR analysis: `python -m dependency_analyzer --pr-url https://github.com/owner/repo/pull/123`
- CI/CD: `python -m dependency_analyzer --diff --quiet --format json`
- Multi-format export: `python -m dependency_analyzer --format csv,json,html`
"""

import argparse
import os
from pathlib import Path

from .core import AdvancedDependencyAnalyzer, DependencyAnalyzer
from .diff_analyzer import DiffAnalyzer


def create_parser() -> argparse.ArgumentParser:
    """Create command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Analyze project dependencies across multiple languages",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze current directory and export to CSV
  python -m dependency_analyzer

  # Analyze specific project
  python -m dependency_analyzer /path/to/project

  # Export to multiple formats
  python -m dependency_analyzer --format json,csv,html

  # Use advanced features
  python -m dependency_analyzer --advanced --find-conflicts

  # Custom project name and output directory
  python -m dependency_analyzer --name "My Project" --output ./reports/
        """
    )
    
    parser.add_argument(
        'path',
        nargs='?',
        default='.',
        help='Path to project directory (default: current directory)'
    )
    
    parser.add_argument(
        '--name', '-n',
        help='Project name (default: directory name)'
    )
    
    parser.add_argument(
        '--output', '-o',
        default='.',
        help='Output directory for reports (default: current directory)'
    )
    
    parser.add_argument(
        '--format', '-f',
        default='csv',
        help='Export format(s): csv,json,md,html (comma-separated, default: csv)'
    )
    
    parser.add_argument(
        '--advanced', '-a',
        action='store_true',
        help='Use advanced analyzer with additional features'
    )
    
    parser.add_argument(
        '--find-conflicts',
        action='store_true', 
        help='Find and report version conflicts'
    )
    
    parser.add_argument(
        '--find-duplicates',
        action='store_true',
        help='Find and report duplicate dependencies'
    )
    
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Show detailed statistics'
    )
    
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Suppress output (only show errors)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose output'
    )
    
    # Diff analysis options
    parser.add_argument(
        '--diff',
        action='store_true',
        help='Analyze dependency changes in git diff'
    )
    
    parser.add_argument(
        '--base-ref',
        default='main',
        help='Base git reference for diff (default: main)'
    )
    
    parser.add_argument(
        '--head-ref', 
        default='HEAD',
        help='Head git reference for diff (default: HEAD)'
    )
    
    parser.add_argument(
        '--pr-url',
        help='GitHub PR URL to analyze (e.g., https://github.com/owner/repo/pull/123)'
    )
    
    parser.add_argument(
        '--github-token',
        help='GitHub token for PR analysis (or set GITHUB_TOKEN env var)'
    )
    
    parser.add_argument(
        '--diff-file',
        help='Path to diff file to analyze'
    )
    
    return parser


def analyze_diff_mode(args, project_path: Path, output_dir: Path) -> int:
    """Handle diff analysis mode."""
    try:
        diff_analyzer = DiffAnalyzer()
        
        if not args.quiet:
            print("🔍 Analyzing dependency changes...")
        
        # Determine which diff analysis to perform
        if args.pr_url:
            github_token = args.github_token or os.getenv('GITHUB_TOKEN')
            if not args.quiet:
                print(f"📊 Analyzing GitHub PR: {args.pr_url}")
            report = diff_analyzer.analyze_pr_diff(args.pr_url, github_token)
        
        elif args.diff_file:
            if not args.quiet:
                print(f"📄 Analyzing diff file: {args.diff_file}")
            with open(args.diff_file) as f:
                diff_content = f.read()
            report = diff_analyzer.analyze_diff_text(diff_content, project_path)
        
        else:  # Git diff mode
            if not args.quiet:
                print(f"📊 Analyzing git diff: {args.base_ref}...{args.head_ref}")
            report = diff_analyzer.analyze_git_diff(args.base_ref, args.head_ref, project_path)
        
        # Print report
        if not args.quiet:
            diff_analyzer.print_diff_report(report)
        
        # Export diff report if requested
        if args.format != 'csv':  # Only support basic formats for diff reports
            formats = [fmt.strip() for fmt in args.format.split(',')]
            for format_name in formats:
                if format_name in ['json', 'csv']:
                    output_file = output_dir / f"dependency_changes.{format_name}"
                    export_diff_report(report, output_file, format_name)
                    if not args.quiet:
                        print(f"📄 Exported {format_name.upper()} diff report: {output_file}")
        
        # Return appropriate exit code
        if report.total_changes > 0:
            if not args.quiet:
                print(f"\n✅ Found {report.total_changes} dependency changes")
            return 0
        else:
            if not args.quiet:
                print("\n✅ No dependency changes found")
            return 0
            
    except Exception as e:
        print(f"❌ Error during diff analysis: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def export_diff_report(report, output_path: Path, format_name: str) -> None:
    """Export diff report to specified format."""
    if format_name == 'json':
        import json
        
        data = {
            'summary': {
                'total_changes': report.total_changes,
                'added': len(report.added_dependencies),
                'removed': len(report.removed_dependencies), 
                'updated': len(report.updated_dependencies),
                'files_changed': [str(f) for f in report.files_changed]
            },
            'changes': {
                'added': [
                    {
                        'name': change.dependency.name,
                        'version': change.new_version,
                        'language': change.dependency.language.value,
                        'type': change.dependency.dependency_type.value,
                        'file': str(change.file_path),
                        'line': change.line_number
                    }
                    for change in report.added_dependencies
                ],
                'removed': [
                    {
                        'name': change.dependency.name,
                        'version': change.old_version,
                        'language': change.dependency.language.value,
                        'type': change.dependency.dependency_type.value,
                        'file': str(change.file_path),
                        'line': change.line_number
                    }
                    for change in report.removed_dependencies
                ],
                'updated': [
                    {
                        'name': change.dependency.name,
                        'old_version': change.old_version,
                        'new_version': change.new_version,
                        'language': change.dependency.language.value,
                        'type': change.dependency.dependency_type.value,
                        'file': str(change.file_path),
                        'line': change.line_number
                    }
                    for change in report.updated_dependencies
                ]
            }
        }
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    elif format_name == 'csv':
        import csv
        
        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'Change Type', 'Dependency Name', 'Old Version', 'New Version', 
                'Language', 'Dependency Type', 'File', 'Line'
            ])
            
            for change in report.added_dependencies:
                writer.writerow([
                    'ADDED', change.dependency.name, '', change.new_version,
                    change.dependency.language.value, change.dependency.dependency_type.value,
                    str(change.file_path), change.line_number
                ])
            
            for change in report.removed_dependencies:
                writer.writerow([
                    'REMOVED', change.dependency.name, change.old_version, '',
                    change.dependency.language.value, change.dependency.dependency_type.value,
                    str(change.file_path), change.line_number
                ])
            
            for change in report.updated_dependencies:
                writer.writerow([
                    'UPDATED', change.dependency.name, change.old_version, change.new_version,
                    change.dependency.language.value, change.dependency.dependency_type.value,
                    str(change.file_path), change.line_number
                ])


def main():
    """Main CLI function."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Setup paths
    project_path = Path(args.path).resolve()
    output_dir = Path(args.output).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if not project_path.exists():
        print(f"❌ Error: Project path does not exist: {project_path}")
        return 1
    
    # Handle diff analysis mode
    if args.diff or args.pr_url or args.diff_file:
        return analyze_diff_mode(args, project_path, output_dir)
    
    # Initialize analyzer
    if args.advanced:
        analyzer = AdvancedDependencyAnalyzer()
    else:
        analyzer = DependencyAnalyzer()
    
    if not args.quiet:
        print(f"🔍 Analyzing dependencies in: {project_path}")
        if args.verbose:
            supported_languages = analyzer.get_supported_languages()
            print(f"🔧 Supported languages: {', '.join(lang.value for lang in supported_languages)}")
    
    try:
        # Analyze project
        report = analyzer.analyze_project(project_path, args.name)
        
        if not args.quiet:
            analyzer.print_summary(report)
        
        # Export reports
        formats = [fmt.strip() for fmt in args.format.split(',')]
        exported_files = []
        
        project_name_safe = report.project_name.replace(' ', '_').replace('/', '_')
        
        for format_name in formats:
            if format_name in analyzer.get_supported_formats():
                output_file = output_dir / f"{project_name_safe}_dependencies.{format_name}"
                analyzer.export_report(report, output_file, format_name)
                exported_files.append(output_file)
                
                if not args.quiet:
                    print(f"📄 Exported {format_name.upper()} report: {output_file}")
            else:
                print(f"⚠️  Warning: Unsupported format '{format_name}' skipped")
        
        # Advanced features
        if args.advanced and (args.find_conflicts or args.find_duplicates or args.stats):
            advanced_analyzer = analyzer if isinstance(analyzer, AdvancedDependencyAnalyzer) else AdvancedDependencyAnalyzer()
            
            if args.find_conflicts:
                conflicts = advanced_analyzer.find_version_conflicts(report)
                if conflicts:
                    print(f"\n⚠️  Version Conflicts Found ({len(conflicts)}):")
                    for name, versions in conflicts.items():
                        print(f"   {name}:")
                        for version_info in versions:
                            print(f"     - {version_info['version']} in {version_info['source']} ({version_info['type']})")
                else:
                    print("\n✅ No version conflicts found")
            
            if args.find_duplicates:
                duplicates = advanced_analyzer.find_duplicate_dependencies(report)
                if duplicates:
                    print(f"\n📦 Duplicate Dependencies Found ({len(duplicates)}):")
                    for name, occurrences in duplicates.items():
                        print(f"   {name}:")
                        for occ in occurrences:
                            print(f"     - {occ['version']} in {occ['source']} ({occ['type']})")
                else:
                    print("\n✅ No duplicate dependencies found")
            
            if args.stats:
                stats = advanced_analyzer.get_dependency_statistics(report)
                print("\n📊 Detailed Statistics:")
                print(f"   Total Dependencies: {stats['total']}")
                print(f"   Duplicate Dependencies: {stats['duplicates']}")
                print(f"   Version Conflicts: {stats['version_conflicts']}")
                if stats['largest_category']:
                    print(f"   Largest Category: {stats['largest_category'][0]} ({stats['largest_category'][1]} deps)")
                if stats['most_common_language']:
                    print(f"   Primary Language: {stats['most_common_language'][0].value} ({stats['most_common_language'][1]} deps)")
        
        if not args.quiet:
            print(f"\n✅ Analysis complete! Generated {len(exported_files)} report(s)")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit(main())