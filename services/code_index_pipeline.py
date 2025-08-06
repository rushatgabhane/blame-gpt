import logging
from collections import defaultdict
from pathlib import Path

import pathspec

from libs.llm import llmNano
from libs.treesitter.extractors import PythonEntityExtractor
from models.models import ProjectStructure

logger = logging.getLogger(__name__)


class CodeIndexPipeline:
    """Pipeline for analyzing entire codebases and extracting structure"""

    def __init__(self, root_path: str, project_name: str | None = None):
        self.extractor = PythonEntityExtractor()
        self.root = Path(root_path)
        self.root_path = root_path
        self.project_name = project_name or self.root.name

        # Load .gitignore patterns
        self.gitignore_spec = self._load_gitignore()

    async def analyze_codebase(self) -> ProjectStructure:
        """Analyze entire codebase and extract high-level structure"""
        if not self.root.exists():
            raise ValueError(f"Path {self.root_path} does not exist")

        file_analyses, languages = self._analyze_python_files()
        logger.info("extraction done")

        self._resolve_call_relationships(file_analyses)
        logger.info("resolved call relations")

        call_graph = self._build_call_graph(file_analyses)
        logger.info("resolved call graph")

        architecture_summary = self._generate_summary(file_analyses)
        logger.info("resolved arch summary")

        file_tree = self._generate_file_tree()
        logger.info("generated file tree")

        key_components = await self._identify_key_components(file_analyses, file_tree)
        logger.info("resolved key components")

        return ProjectStructure(
            name=self.project_name,
            root_path=self.root_path,
            total_files=len(file_analyses),
            languages=dict(languages),
            file_analyses=file_analyses,
            architecture_summary=architecture_summary,
            key_components=key_components,
            call_graph=call_graph,
            file_tree=file_tree,
        )

    def _analyze_python_files(self) -> tuple[list, defaultdict]:
        """Find and analyze all Python files in the project"""
        python_files = list(self.root.rglob("*.py"))
        logger.info(f"Found {len(python_files)} Python files")

        file_analyses: list = []
        languages: defaultdict[str, int] = defaultdict(int)

        for file_path in python_files:
            if self._should_skip_file(file_path):
                continue

            analysis = self.extractor.extract_from_file(file_path)
            if analysis:
                logger.info(f"extracted from filepath {file_path}")
                file_analyses.append(analysis)
                languages[analysis.language] += 1

        return file_analyses, languages

    def _load_gitignore(self) -> pathspec.PathSpec | None:
        """Load .gitignore patterns from the root directory"""
        gitignore_path = self.root / ".gitignore"
        if not gitignore_path.exists():
            return None
        try:
            with open(gitignore_path, encoding="utf-8") as f:
                patterns = f.read().splitlines()
            spec = pathspec.PathSpec.from_lines("gitwildmatch", patterns)
            logger.info(f"Loaded .gitignore with {len(patterns)} patterns")
            return spec
        except Exception as e:
            logger.warning(f"Failed to load .gitignore: {e}")
            return None

    def _should_skip_file(self, file_path: Path) -> bool:
        if self.gitignore_spec:
            relative_path = str(file_path.relative_to(self.root))
            if self.gitignore_spec.match_file(relative_path):
                return True

        file_str = str(file_path).lower()
        if "test" in file_str or "tests" in file_str:
            return True

        # Fallback ignore
        ignored_dirs = {".git", "build", "__pycache__", "node_modules", "venv", "env", ".pytest_cache"}
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

    def _generate_summary(self, analyses) -> str:
        """Generate simple architecture summary"""
        total_functions = sum(len([e for e in a.entities if e.type in ["function", "method"]]) for a in analyses)
        total_classes = sum(len([e for e in a.entities if e.type == "class"]) for a in analyses)

        return f"Python project '{self.project_name}' with {len(analyses)} files, {total_classes} classes, {total_functions} functions/methods"

    async def _identify_key_components(self, analyses, file_tree: str) -> list[dict]:
        """Identify key files by import count and LLM analysis of directory structure"""
        logger.info(f"Starting key component identification for {len(analyses)} files")
        file_analysis = {}

        for i, analysis in enumerate(analyses):
            if i % 10 == 0:
                logger.info(f"Processing file {i + 1}/{len(analyses)}: {analysis.file_path}")

            import_count = self._count_file_imports(analysis, analyses)
            file_functions = self._analyze_file_functions(analysis)

            file_analysis[analysis.file_path] = {
                "import_count": import_count,
                "total_functions": len(file_functions),
                "functions_with_callers": len([f for f in file_functions if f["called_by_count"] > 0]),
                "top_functions": file_functions[:50],  # Top 50 functions
                "total_imports": len(analysis.imports),
            }

        logger.info("Completed file analysis processing, calling LLM for important files")
        llm_important_files = await self._get_llm_important_files(file_tree)

        logger.info("Building final component list with LLM insights")
        return self._build_component_list_with_llm(file_analysis, llm_important_files)

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
        sorted_files = sorted(file_analysis.items(), key=lambda x: x[1]["import_count"], reverse=True)[:100]

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

    async def _get_llm_important_files(self, file_tree: str) -> list[str]:
        """Use LLM to identify architecturally important files from directory structure"""
        try:
            from libs.prompt_templates.identify_important_files import (
                format_identify_important_files_prompt,
                important_files_parser,
            )

            prompt = format_identify_important_files_prompt(file_tree)
            logger.info(f"File tree prompt length: {len(prompt)} characters (~{len(prompt) // 4} tokens)")

            logger.info("Calling LLM to identify important files...")
            response = await llmNano.ainvoke(prompt)
            logger.info("LLM call completed, parsing response...")
            
            parsed_response = important_files_parser.invoke(response)
            logger.info("Response parsed successfully")

            # Log token usage if available
            token_usage = response.response_metadata["token_usage"]
            logger.info(
                f"File tree LLM usage - Input: {token_usage.get('prompt_tokens', 'N/A')}, "
                f"Output: {token_usage.get('completion_tokens', 'N/A')}, "
                f"Total: {token_usage.get('total_tokens', 'N/A')}"
            )

            logger.info(f"LLM identified {len(parsed_response.files)} important files")
            return parsed_response.files

        except Exception as e:
            logger.warning(f"Failed to get LLM important files: {e}")
            return []

    def _build_component_list_with_llm(self, file_analysis: dict, llm_important_files: list[str]) -> list[dict]:
        """Build component list combining import analysis and LLM insights"""
        components = []

        def create_component(file_path: str, info: dict, comp_type: str) -> dict:
            return {
                "file": file_path,
                "type": comp_type,
                "import_count": info["import_count"],
                "total_functions": info["total_functions"],
                "functions_with_callers": info["functions_with_callers"],
                "total_file_imports": info["total_imports"],
                "top_functions": info["top_functions"],
            }

        # 1. LLM-identified important files (priority)
        for relative_path in llm_important_files:
            full_path = str(self.root / relative_path)
            logger.info(f"LLM important file: {relative_path} -> {full_path}")
            if full_path in file_analysis:
                info = file_analysis[full_path]
                components.append(create_component(full_path, info, "llm_identified_important"))
            else:
                logger.warning(f"LLM file not found in analysis: {full_path}")

        # 2. High import count files (fill remaining slots)
        sorted_files = sorted(file_analysis.items(), key=lambda x: x[1]["import_count"], reverse=True)
        for file_path, info in sorted_files:
            if info["import_count"] > 0 and not any(comp["file"] == file_path for comp in components):
                components.append(create_component(file_path, info, "high_import_module"))

        return components[:100]

    def _has_python_files(self, path: Path) -> bool:
        try:
            return any(not self._should_skip_file(item) for item in path.rglob("*.py"))
        except PermissionError:
            return False

    def _generate_file_tree(self) -> str:
        """Generate a file tree showing only Python files and directories containing them"""
        lines = []

        def add_files(path: Path, prefix: str = ""):
            if self._should_skip_file(path):
                return

            try:
                items = sorted([item for item in path.iterdir() if not self._should_skip_file(item)])

                dirs_with_py = [item for item in items if item.is_dir() and self._has_python_files(item)]
                py_files = [item for item in items if item.is_file() and item.suffix == ".py"]

                for item in dirs_with_py:
                    lines.append(f"{prefix} {item.name}/")
                    add_files(item, prefix + " ")

                for item in py_files:
                    lines.append(f"{prefix} {item.name}")

            except PermissionError:
                pass

        lines.append(f"{self.root.name}/")
        add_files(self.root)

        return "\n".join(lines)


async def run(codebase_path: str, project_name: str | None = None):
    """Main entry point for code indexing pipeline"""
    pipeline = CodeIndexPipeline(codebase_path, project_name)

    try:
        logger.info(f"Starting code indexing for {codebase_path}")
        project_structure = await pipeline.analyze_codebase()

        # with open("project_structure.json", "w") as f:
        #     json.dump(project_structure.model_dump(), f, indent=2, default=str)

        logger.info(f"Call graph has {len(project_structure.call_graph)} functions")

        return project_structure

    except Exception as e:
        logger.error(f"Code indexing failed: {e}")
        raise
