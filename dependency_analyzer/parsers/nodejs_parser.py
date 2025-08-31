"""
Node.js dependency parser for package.json and related files.

WHAT IT DOES:
- Parses Node.js dependency files (package.json, package-lock.json, etc.)
- Extracts dependencies from all sections (dependencies, devDependencies, etc.)
- Handles NPM version ranges and semantic versioning
- Provides foundation for lockfile analysis

HOW IT WORKS:
1. **JSON Parsing**: Parses package.json using standard JSON library
2. **Section Processing**: Extracts from dependencies, devDependencies, peerDependencies, optionalDependencies
3. **Type Classification**: Maps JSON sections to dependency types
4. **Version Handling**: Preserves NPM version range specifications
5. **Object Creation**: Creates structured Dependency objects

SUPPORTED FILES:
- package.json (main NPM package descriptor)
- package-lock.json (planned - for detailed version info)
- yarn.lock (planned - Yarn lockfile)
- pnpm-lock.yaml (planned - PNPM lockfile)

DEPENDENCY SECTIONS:
- dependencies → DependencyType.RUNTIME
- devDependencies → DependencyType.DEVELOPMENT  
- peerDependencies → DependencyType.PEER
- optionalDependencies → DependencyType.OPTIONAL

VERSION FORMATS:
- Exact: "1.0.0"
- Caret: "^1.0.0" (compatible version)
- Tilde: "~1.0.0" (reasonably close to)
- Range: ">=1.0.0 <2.0.0"
- Latest: "latest", "*"
- GitHub: "user/repo", "github:user/repo"
- File/URL: "file:../path", "http://..."

ERROR HANDLING:
- Graceful handling of malformed JSON
- Continues processing if individual sections fail
- Logs warnings for unparseable content
- Returns empty list on critical failures

FUTURE ENHANCEMENTS:
- package-lock.json analysis for exact versions and dependency tree
- yarn.lock parsing for Yarn-managed projects  
- pnpm-lock.yaml parsing for PNPM projects
- Workspace and monorepo dependency resolution
- Bundled dependency detection
"""

import json
from pathlib import Path

from ..models import Dependency, DependencyType, Language
from .base_parser import BaseParser


class NodeJSParser(BaseParser):
    """Parser for Node.js dependency files."""
    
    @property
    def language(self) -> Language:
        return Language.NODEJS
    
    @property
    def supported_files(self) -> set[str]:
        return {
            'package.json',
            'package-lock.json',
            'yarn.lock',
            'pnpm-lock.yaml'
        }
    
    def parse(self, file_path: Path) -> list[Dependency]:
        """Parse Node.js dependencies."""
        try:
            self._validate_file(file_path)
            
            if file_path.name == 'package.json':
                return self._parse_package_json(file_path)
            elif file_path.name == 'package-lock.json':
                return self._parse_package_lock_json(file_path)
            # TODO: Add yarn.lock and pnpm-lock.yaml parsers
            else:
                return []
                
        except Exception as e:
            return self._handle_parse_error(file_path, e)
    
    def _parse_package_json(self, file_path: Path) -> list[Dependency]:
        """Parse package.json dependencies."""
        dependencies = []
        
        try:
            with open(file_path, encoding='utf-8') as f:
                data = json.load(f)
            
            # Parse different dependency types
            dep_sections = [
                ('dependencies', DependencyType.RUNTIME),
                ('devDependencies', DependencyType.DEVELOPMENT),
                ('peerDependencies', DependencyType.PEER),
                ('optionalDependencies', DependencyType.OPTIONAL)
            ]
            
            for section_name, dep_type in dep_sections:
                deps = data.get(section_name, {})
                for name, version in deps.items():
                    dependency = Dependency(
                        name=name,
                        version=version,
                        language=self.language,
                        dependency_type=dep_type,
                        source_file=file_path,
                        metadata={
                            'section': section_name,
                            'package_json_path': str(file_path)
                        }
                    )
                    dependencies.append(dependency)
                    
        except (json.JSONDecodeError, Exception) as e:
            return self._handle_parse_error(file_path, e)
        
        return dependencies
    
    def _parse_package_lock_json(self, file_path: Path) -> list[Dependency]:
        """Parse package-lock.json for more detailed dependency info."""
        # TODO: Implement package-lock.json parsing
        # This would provide exact versions, dependency tree, and resolved URLs
        print(f"Info: package-lock.json parsing not yet implemented for {file_path}")
        return []
    
    def _parse_yarn_lock(self, file_path: Path) -> list[Dependency]:
        """Parse yarn.lock for Yarn-managed dependencies."""
        # TODO: Implement yarn.lock parsing
        print(f"Info: yarn.lock parsing not yet implemented for {file_path}")
        return []
    
    def _parse_pnpm_lock(self, file_path: Path) -> list[Dependency]:
        """Parse pnpm-lock.yaml for PNPM-managed dependencies."""
        # TODO: Implement pnpm-lock.yaml parsing
        print(f"Info: pnpm-lock.yaml parsing not yet implemented for {file_path}")
        return []