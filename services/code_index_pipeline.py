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

        file_analyses, languages = self._analyze_python_files(root)

        self._resolve_call_relationships(file_analyses)

        call_graph = self._build_call_graph(file_analyses)
        architecture_summary = self._generate_summary(file_analyses, project_name)
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

    def _analyze_python_files(self, root: Path) -> tuple[list, defaultdict]:
        """Find and analyze all Python files in the project"""
        python_files = list(root.rglob("*.py"))
        logger.info(f"Found {len(python_files)} Python files")

        file_analyses = []
        languages = defaultdict(int)

        for file_path in python_files:
            if self._should_skip_file(file_path):
                continue

            analysis = self.extractor.extract_from_file(file_path)
            if analysis:
                file_analyses.append(analysis)
                languages[analysis.language] += 1

        return file_analyses, languages

    def _should_skip_file(self, file_path: Path) -> bool:
        """Check if file should be skipped during analysis"""
        ignored_dirs = {".git", "__pycache__", "node_modules", "venv", "env", ".pytest_cache"}
        return any(part.startswith(".") or part in ignored_dirs for part in file_path.parts)

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
        # Build lookup maps for fast resolution
        name_to_id, entity_map = self._build_entity_maps(file_analyses)

        # Process each function/method to resolve its calls
        for analysis in file_analyses:
            for entity in analysis.entities:
                if entity.type in ["function", "method"]:
                    self._process_entity_calls(entity, name_to_id, entity_map)

    def _build_entity_maps(self, file_analyses) -> tuple[dict, dict]:
        """Build name-to-ID and entity mapping for call resolution"""
        name_to_id = {}
        entity_map = {}

        for analysis in file_analyses:
            for entity in analysis.entities:
                if entity.type in ["function", "method"]:
                    entity_map[entity.id] = entity
                    name_to_id[entity.name] = entity.id

        return name_to_id, entity_map

    def _process_entity_calls(self, entity, name_to_id: dict, entity_map: dict) -> None:
        """Process all calls for a single entity"""
        for call in entity.calls:
            target_id = self._resolve_call_target(call.target, name_to_id)

            if target_id:
                # Mark as internal call and update relationships
                call.target = target_id
                call.is_internal = True
                entity_map[target_id].called_by.append(entity.id)
            else:
                # Keep as external call
                call.is_internal = False

    def _resolve_call_target(self, call_target: str, name_to_id: dict) -> str | None:
        """Resolve a call target to entity ID if it's internal"""
        # Try exact match first
        if call_target in name_to_id:
            return name_to_id[call_target]

        # Handle module.function calls - extract just the function name
        if "." in call_target:
            func_name = call_target.split(".")[-1]
            if func_name in name_to_id:
                return name_to_id[func_name]

        return None

    def _generate_summary(self, analyses, project_name: str) -> str:
        """Generate simple architecture summary"""
        total_functions = sum(len([e for e in a.entities if e.type in ["function", "method"]]) for a in analyses)
        total_classes = sum(len([e for e in a.entities if e.type == "class"]) for a in analyses)

        return f"Python project '{project_name}' with {len(analyses)} files, {total_classes} classes, {total_functions} functions/methods"

    def _identify_key_components(self, analyses) -> list[dict]:
        """Identify key files by import count, with top functions per file"""
        file_analysis = {}

        for analysis in analyses:
            import_count = self._count_file_imports(analysis, analyses)
            file_functions = self._analyze_file_functions(analysis)

            file_analysis[analysis.file_path] = {
                "import_count": import_count,
                "total_functions": len(file_functions),
                "functions_with_callers": len([f for f in file_functions if f["called_by_count"] > 0]),
                "top_functions": file_functions[:50],  # Top 50 functions
                "total_imports": len(analysis.imports),
            }

        return self._build_component_list(file_analysis)

    def _count_file_imports(self, target_analysis, all_analyses) -> int:
        """Count how many other files import/call functions from target file"""
        import_count = 0
        target_file = target_analysis.file_path

        for other_analysis in all_analyses:
            if other_analysis.file_path == target_file:
                continue

            # Check if any entity in other file calls entities in target file
            for entity in other_analysis.entities:
                if entity.type in ["function", "method"]:
                    for call in entity.calls:
                        if call.is_internal and call.target.startswith(target_file + ":"):
                            import_count += 1
                            break  # Count file only once per calling file

        return import_count

    def _analyze_file_functions(self, analysis) -> list[dict]:
        """Analyze all functions in a file and return sorted by importance"""
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

        # Sort by how many times each function is called (most important first)
        file_functions.sort(key=lambda x: x["called_by_count"], reverse=True)
        return file_functions

    def _build_component_list(self, file_analysis: dict) -> list[dict]:
        """Build final list of key components from file analysis"""
        # Sort files by import count (how many files depend on this file)
        sorted_files = sorted(file_analysis.items(), key=lambda x: x[1]["import_count"], reverse=True)[:50]

        components = []
        for file_path, info in sorted_files:
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

        logger.info(f"Call graph has {len(project_structure.call_graph)} functions")

        return project_structure

    except Exception as e:
        logger.error(f"Code indexing failed: {e}")
        raise
