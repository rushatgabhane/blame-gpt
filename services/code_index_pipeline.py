import logging
from collections import defaultdict
from pathlib import Path

from libs.treesitter.extractors import PythonEntityExtractor
from models.models import ProjectStructure

logger = logging.getLogger(__name__)


class CodeIndexPipeline:
    """Pipeline for analyzing entire codebases and extracting structure"""

    def __init__(self):
        self.extractor = PythonEntityExtractor()

    def analyze_codebase(self, root_path: str, project_name: str | None = None) -> ProjectStructure:
        """Analyze entire codebase and extract high-level structure"""
        root = Path(root_path)
        if not root.exists():
            raise ValueError(f"Path {root_path} does not exist")

        project_name = project_name or root.name
        logger.info(f"Starting analysis of {project_name} at {root_path}")

        # Find all Python files
        python_files = list(root.rglob("*.py"))
        logger.info(f"Found {len(python_files)} Python files")

        # Analyze each file
        file_analyses = []
        languages = defaultdict(int)

        for file_path in python_files:
            # Skip common ignored directories
            if any(
                part.startswith(".") or part in ["__pycache__", "node_modules", "venv", "env"]
                for part in file_path.parts
            ):
                continue

            analysis = self.extractor.extract_from_file(file_path)
            if analysis:
                file_analyses.append(analysis)
                languages[analysis.language] += 1

        # Convert function name calls to entity IDs
        self._resolve_call_relationships(file_analyses)

        # Build call graph using entity IDs
        call_graph = self._build_call_graph(file_analyses)

        # Generate architecture summary
        architecture_summary = self._generate_summary(file_analyses, project_name)

        # Identify key components
        key_components = self._identify_key_components(file_analyses)

        return ProjectStructure(
            name=project_name,
            root_path=root_path,
            total_files=len(file_analyses),
            languages=dict(languages),
            file_analyses=file_analyses,
            architecture_summary=architecture_summary,
            key_components=key_components,
            call_graph=call_graph,
        )

    def _build_call_graph(self, file_analyses) -> dict[str, list[str]]:
        """Build call graph: entity_id -> list of internal entity_ids it calls"""
        call_graph = {}

        for analysis in file_analyses:
            for entity in analysis.entities:
                if entity.type in ["function", "method"]:
                    # Extract only internal call targets for clean call graph
                    internal_targets = [call.target for call in entity.calls if call.is_internal]
                    call_graph[entity.id] = internal_targets

        return call_graph

    def _resolve_call_relationships(self, file_analyses) -> None:
        """Resolve function calls and build called_by relationships"""
        # Create name-to-ID mapping
        name_to_id = {}
        entity_map = {}

        for analysis in file_analyses:
            for entity in analysis.entities:
                if entity.type in ["function", "method"]:
                    entity_map[entity.id] = entity
                    name_to_id[entity.name] = entity.id

        # Resolve calls and build reverse relationships
        for analysis in file_analyses:
            for entity in analysis.entities:
                if entity.type in ["function", "method"]:
                    # Process each FunctionCall object
                    for call in entity.calls:
                        target_id = None

                        # Try exact match first
                        if call.target in name_to_id:
                            target_id = name_to_id[call.target]
                        else:
                            # Handle module.function calls - extract just the function name
                            if "." in call.target:
                                func_name = call.target.split(".")[-1]
                                if func_name in name_to_id:
                                    target_id = name_to_id[func_name]

                        if target_id:
                            # Update target to entity ID and mark as internal
                            call.target = target_id
                            call.is_internal = True
                            # Add to called_by
                            entity_map[target_id].called_by.append(entity.id)
                        else:
                            # Keep as external call
                            call.is_internal = False

    def _generate_summary(self, analyses, project_name: str) -> str:
        """Generate simple architecture summary"""
        total_functions = sum(len([e for e in a.entities if e.type in ["function", "method"]]) for a in analyses)
        total_classes = sum(len([e for e in a.entities if e.type == "class"]) for a in analyses)

        return f"Python project '{project_name}' with {len(analyses)} files, {total_classes} classes, {total_functions} functions/methods"

    def _identify_key_components(self, analyses) -> list[dict]:
        """Identify key files by import count, with top functions per file"""
        # Build file-level analysis
        file_analysis = {}

        for analysis in analyses:
            file_path = analysis.file_path

            # Count imports (how many other files import from this file)
            import_count = 0
            for other_analysis in analyses:
                if other_analysis.file_path != file_path:
                    # Check if any entity in other file calls entities in this file
                    for other_entity in other_analysis.entities:
                        if other_entity.type in ["function", "method"]:
                            for call in other_entity.calls:
                                if call.is_internal and call.target.startswith(file_path + ":"):
                                    import_count += 1
                                    break  # Count file only once per calling file

            # Get all functions in this file with their dependency counts
            file_functions = []
            for entity in analysis.entities:
                if entity.type in ["function", "method"]:
                    file_functions.append(
                        {
                            "name": entity.name,
                            "id": entity.id,
                            "called_by_count": len(entity.called_by),
                            "calls_count": len([c for c in entity.calls if c.is_internal]),
                            "external_calls_count": len([c for c in entity.calls if not c.is_internal]),
                            "start_line": entity.start_line,
                            "end_line": entity.end_line,
                        }
                    )

            # Sort functions by called_by_count and take top 50
            file_functions.sort(key=lambda x: x["called_by_count"], reverse=True)
            top_50_functions = file_functions[:50]

            file_analysis[file_path] = {
                "import_count": import_count,
                "total_functions": len(file_functions),
                "functions_with_callers": len([f for f in file_functions if f["called_by_count"] > 0]),
                "top_functions": top_50_functions,
                "total_imports": len(analysis.imports),
            }

        # Sort files by import count (how many files depend on this file)
        sorted_files = sorted(file_analysis.items(), key=lambda x: x[1]["import_count"], reverse=True)[
            :50
        ]  # Top 50 files

        components = []
        for file_path, info in sorted_files:
            if info["import_count"] > 0 or info["functions_with_callers"] > 0:  # Only include files that are used
                components.append(
                    {
                        "file": file_path,
                        "type": "high_import_module",
                        "import_count": info["import_count"],
                        "total_functions": info["total_functions"],
                        "functions_with_callers": info["functions_with_callers"],
                        "total_file_imports": info["total_imports"],
                        "top_functions": info["top_functions"],
                    }
                )

        return components


async def run(codebase_path: str, project_name: str | None = None):
    """Main entry point for code indexing pipeline"""
    pipeline = CodeIndexPipeline()

    try:
        logger.info(f"Starting code indexing for {codebase_path}")
        project_structure = pipeline.analyze_codebase(codebase_path, project_name)

        # Print summary
        logger.info(f"Analysis completed: {project_structure.architecture_summary}")
        logger.info("Key components:")
        for component in project_structure.key_components:
            logger.info(
                f"  - {Path(component['file']).name}: {component['import_count']} imports, {component['functions_with_callers']} callable functions"
            )

        logger.info(f"Call graph has {len(project_structure.call_graph)} functions")

        return project_structure

    except Exception as e:
        logger.error(f"Code indexing failed: {e}")
        raise
