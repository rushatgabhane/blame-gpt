"""
Default rule-based dependency categorizer.

WHAT IT DOES:
- Provides comprehensive rule-based categorization for common dependencies
- Uses pattern matching on dependency names to assign categories
- Supports both universal (cross-language) and language-specific rules
- Covers 20+ categories including Web Framework, AI/ML, Testing, Database, etc.

HOW IT WORKS:
1. **Rule Hierarchy**: Checks language-specific rules first, then universal rules
2. **Pattern Matching**: String contains matching for package names
3. **Category Assignment**: Returns first matching category or "Other"
4. **Rule Structure**: Organized by language with category → patterns mapping

CATEGORIZATION STRATEGY:

Universal Categories (all languages):
- Web Framework: fastapi, react, express, django, angular, vue, svelte
- Testing: jest, pytest, mocha, unittest, cypress, karma, jasmine
- Database: postgres, mongo, redis, mysql, sqlite, sequelize, mongoose
- HTTP/Network: requests, axios, fetch, websocket, urllib, aiohttp
- Security/Crypto: jwt, bcrypt, crypto, ssl, oauth, argon2
- CLI/Utilities: click, commander, yargs, inquirer, chalk, rich, typer
- Development Tools: lint, prettier, eslint, babel, webpack, ruff, mypy
- Logging: winston, bunyan, pino, debug, trace
- Configuration: config, env, dotenv, settings
- Documentation: doc, markdown, sphinx, jsdoc

Language-Specific Categories:

Python-Specific:
- AI/ML: openai, langchain, transformers, torch, tensorflow, sklearn, pandas
- Data Processing: numpy, scipy, matplotlib, seaborn, plotly, pillow
- Jupyter/Notebooks: jupyter, ipython, ipykernel, notebook, jupyterlab
- Async/Concurrency: asyncio, aiohttp, aiofiles, anyio, trio
- Type System: mypy, pydantic, typing, dataclasses, attrs

Node.js-Specific:
- Build Tools: webpack, rollup, vite, parcel, esbuild, babel, typescript
- UI Components: material, antd, chakra, mantine, bootstrap, tailwind
- State Management: redux, mobx, zustand, recoil, jotai
- Routing: router, react-router, vue-router, reach-router
- Package Management: npm, yarn, pnpm, lerna, rush

EXTENSIBILITY:
- Easy to add new categories by extending category_rules
- Simple to add new languages with their specific patterns
- Can be subclassed for domain-specific customizations
- Patterns support both string matching and regex (future)

FALLBACK BEHAVIOR:
- Dependencies that don't match any pattern are categorized as "Other"
- Ensures all dependencies receive a category assignment
- Provides clear extension point for handling unknown packages
"""

from re import Pattern

from ..models import Dependency, Language
from .base_categorizer import BaseCategorizer


class DefaultCategorizer(BaseCategorizer):
    """Default rule-based categorizer supporting multiple languages."""
    
    def __init__(self):
        self.category_rules = self._build_category_rules()
    
    def categorize(self, dependency: Dependency) -> str:
        """Categorize dependency based on name patterns and language."""
        name_lower = dependency.name.lower()
        
        # Check language-specific rules first
        if dependency.language in self.category_rules:
            for category, patterns in self.category_rules[dependency.language].items():
                if self._matches_patterns(name_lower, patterns):
                    return category
        
        # Check universal rules
        if 'universal' in self.category_rules:
            for category, patterns in self.category_rules['universal'].items():
                if self._matches_patterns(name_lower, patterns):
                    return category
        
        return "Other"
    
    def _matches_patterns(self, name: str, patterns: list[str]) -> bool:
        """Check if name matches any of the patterns."""
        for pattern in patterns:
            if isinstance(pattern, str):
                if pattern in name:
                    return True
            elif isinstance(pattern, Pattern):
                if pattern.search(name):
                    return True
        return False
    
    def _build_category_rules(self) -> dict:
        """Build categorization rules for different languages."""
        return {
            # Universal rules (apply to all languages)
            'universal': {
                "Web Framework": [
                    "fastapi", "starlette", "flask", "django", "express", "koa", "hapi",
                    "react", "vue", "angular", "svelte", "next", "nuxt", "gatsby"
                ],
                "Testing": [
                    "test", "jest", "mocha", "chai", "jasmine", "karma", "cypress", 
                    "pytest", "unittest", "nose", "tox", "coverage", "mock"
                ],
                "Database": [
                    "sql", "mongo", "redis", "postgres", "mysql", "sqlite", "orm",
                    "sequelize", "mongoose", "typeorm", "prisma", "knex"
                ],
                "HTTP/Network": [
                    "http", "request", "fetch", "axios", "curl", "websocket", "socket",
                    "client", "urllib", "aiohttp"
                ],
                "CLI/Utilities": [
                    "cli", "command", "terminal", "console", "click", "commander", 
                    "yargs", "inquirer", "chalk", "colors", "rich", "typer"
                ],
                "Development Tools": [
                    "lint", "format", "prettier", "eslint", "babel", "webpack", 
                    "rollup", "vite", "parcel", "ruff", "black", "isort", "mypy"
                ],
                "Security/Crypto": [
                    "crypto", "hash", "encrypt", "decrypt", "jwt", "auth", "oauth",
                    "bcrypt", "passport", "security", "ssl", "tls"
                ],
                "Logging": [
                    "log", "winston", "bunyan", "pino", "debug", "trace"
                ],
                "Configuration": [
                    "config", "env", "dotenv", "settings", "options"
                ],
                "Documentation": [
                    "doc", "docs", "readme", "markdown", "sphinx", "jsdoc"
                ]
            },
            
            # Python-specific rules
            Language.PYTHON: {
                "Web Framework": [
                    "fastapi", "django", "flask", "tornado", "pyramid", "cherrypy",
                    "bottle", "falcon", "sanic", "quart", "starlette", "uvicorn", "gunicorn"
                ],
                "AI/ML": [
                    "openai", "langchain", "tiktoken", "transformers", "torch", "tensorflow",
                    "sklearn", "scikit", "pandas", "numpy", "scipy", "matplotlib", "seaborn",
                    "keras", "xgboost", "lightgbm", "catboost", "huggingface"
                ],
                "Data Processing": [
                    "pandas", "numpy", "scipy", "matplotlib", "seaborn", "plotly",
                    "pillow", "opencv", "imageio", "scikit-image", "dask", "polars"
                ],
                "Database": [
                    "sqlalchemy", "django-orm", "peewee", "tortoise", "databases",
                    "asyncpg", "psycopg", "pymongo", "redis-py", "sqlite3"
                ],
                "Jupyter/Notebooks": [
                    "jupyter", "ipython", "ipykernel", "notebook", "jupyterlab", 
                    "nbconvert", "nbformat", "ipywidgets"
                ],
                "Async/Concurrency": [
                    "asyncio", "aiohttp", "aiofiles", "anyio", "trio", "uvloop"
                ],
                "Code Parsing": [
                    "ast", "tree-sitter", "parser", "lexer", "tokenizer", "jedi", "rope"
                ],
                "Type System": [
                    "typing", "mypy", "pydantic", "dataclasses", "attrs", "types-"
                ],
                "Package Management": [
                    "pip", "setuptools", "wheel", "poetry", "pipenv", "conda", "mamba"
                ]
            },
            
            # Node.js-specific rules  
            Language.NODEJS: {
                "Web Framework": [
                    "express", "koa", "hapi", "fastify", "nest", "next", "nuxt",
                    "react", "vue", "angular", "svelte", "gatsby", "remix"
                ],
                "Build Tools": [
                    "webpack", "rollup", "vite", "parcel", "esbuild", "swc",
                    "babel", "typescript", "tsc", "gulp", "grunt"
                ],
                "Package Management": [
                    "npm", "yarn", "pnpm", "lerna", "rush", "nx"
                ],
                "State Management": [
                    "redux", "mobx", "zustand", "recoil", "jotai", "valtio"
                ],
                "Routing": [
                    "router", "reach-router", "react-router", "vue-router", "page"
                ],
                "UI Components": [
                    "component", "ui", "material", "antd", "chakra", "mantine",
                    "bootstrap", "tailwind", "styled-components", "emotion"
                ],
                "Validation": [
                    "joi", "yup", "zod", "ajv", "validator", "express-validator"
                ]
            }
        }