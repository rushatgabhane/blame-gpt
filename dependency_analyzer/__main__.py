"""
Entry point for running dependency analyzer as a module.

WHAT IT DOES:
- Provides the entry point for running the dependency analyzer as a Python module
- Enables execution via `python -m dependency_analyzer` command
- Bridges between module execution and CLI interface
- Ensures proper module initialization and error handling

HOW IT WORKS:
1. **Module Entry**: Python's -m flag calls this file when executing the module
2. **CLI Import**: Imports and delegates to the main CLI function
3. **Exit Handling**: Properly handles exit codes from CLI execution
4. **Error Management**: Ensures clean module termination on errors

USAGE:
This file enables all of these command patterns:
- `python -m dependency_analyzer` (basic project analysis)
- `python -m dependency_analyzer --help` (show help)
- `python -m dependency_analyzer --diff` (diff analysis)
- `python -m dependency_analyzer --pr-url URL` (PR analysis)

The file simply imports the CLI main function and delegates all functionality
to the comprehensive command-line interface defined in cli.py.
"""

from .cli import main

if __name__ == '__main__':
    exit(main())