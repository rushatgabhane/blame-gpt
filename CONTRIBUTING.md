# Contributing to BlameGPT 🤝

Thank you for your interest in contributing to BlameGPT! This guide will help you get started with contributing to the project.

## 📋 Table of Contents

- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Code Standards](#code-standards)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Issue Guidelines](#issue-guidelines)
- [Pull Request Process](#pull-request-process)

## 🚀 Getting Started

### Prerequisites

Before contributing, ensure you have:

- **Python 3.12+** installed
- **Node.js 20+** and npm
- **Git** for version control
- **GitHub Personal Access Token** for testing GitHub integrations
- **OpenAI API Key** for testing AI functionality (optional for some contributions)

### Development Environment Setup

#### Quick Setup (Recommended)

#### Setup Steps

1. **Fork and Clone**
   ```bash
   git clone https://github.com/YOUR_USERNAME/blame-gpt.git
   cd blame-gpt
   ```

2. **Set up Python Environment**
   ```bash
   # Install dependencies
   pip install -r requirements.txt
   
   # Set up environment variables
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Set up Frontend Environment**
   ```bash
   cd frontend
   npm install
   cd ..
   ```

4. **Configure Repository Target** (if needed)
   
   By default, BlameGPT is configured to work with the Expensify/App repository. To use it with a different repository, edit `libs/constants.py`:
   
   ```python
   REPO_OWNER = "your-org"
   REPO_NAME = "your-repo"
   ```

5. **Verify Installation**
   ```bash
   # Format code first
   black . --line-length=120
   
   # Build and test frontend
   cd frontend && npm run build && npm run lint && cd ..
   
   # Note: Backend requires valid GitHub token to fully test
   ```

## 🏗️ Development Setup

### Project Structure

```
blame-gpt/
├── controllers/          # FastAPI route handlers
│   ├── blame_controller.py
│   ├── issue_controller.py
│   └── ...
├── frontend/            # React TypeScript frontend
│   ├── src/
│   ├── public/
│   └── package.json
├── libs/                # Shared libraries and utilities
│   ├── github.py        # GitHub API integration
│   ├── llm.py          # LLM utilities
│   └── sqlite/         # Database clients
├── middlewares/         # FastAPI middleware
├── models/              # Pydantic data models
├── services/            # Business logic layer
│   ├── blame_pipeline.py
│   ├── github/
│   └── docs_service/
├── main.py              # FastAPI application entry point
└── requirements.txt     # Python dependencies
```

### Running in Development Mode

#### Development Commands

1. **Backend Development**
   ```bash
   python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```
   - Auto-reloads on file changes
   - API docs available at `http://localhost:8000/docs`

2. **Frontend Development**
   ```bash
   cd frontend
   npm run dev
   ```
   - Hot module replacement enabled
   - Available at `http://localhost:5173`

## 📏 Code Standards

### Python Code Style

We use **Black** for Python code formatting with a line length of 120 characters.

```bash
# Format your code before committing
black . --line-length=120

# Check formatting
black . --line-length=120 --check
```

### Python Code Guidelines

- Follow PEP 8 style guidelines
- Use type hints for function parameters and return values
- Write descriptive variable and function names
- Add docstrings for public functions and classes
- Keep functions focused and concise

**Example:**
```python
from typing import List, Optional
from models.models import Issue

async def process_issue(issue_id: int, db: Database) -> Optional[Issue]:
    """
    Process a GitHub issue and extract relevant information.
    
    Args:
        issue_id: The GitHub issue ID to process
        db: Database connection instance
        
    Returns:
        Processed Issue object or None if not found
    """
    # Implementation here
    pass
```

### TypeScript/React Code Style

- Use TypeScript for all new React components
- Follow React hooks best practices
- Use functional components over class components
- Maintain consistent naming conventions

**Example:**
```typescript
interface BlameResultProps {
  issueId: number;
  culpritPRs: CulpritPullRequest[];
}

const BlameResult: React.FC<BlameResultProps> = ({ issueId, culpritPRs }) => {
  // Component implementation
};
```

### Import Organization

Organize imports in this order:
1. Standard library imports
2. Third-party library imports  
3. Local application imports

```python
# Standard library
import logging
from typing import List, Optional

# Third-party
from fastapi import APIRouter, Request
from pydantic import BaseModel

# Local
from models.models import Issue
from services import blame_pipeline
```

## 🧪 Testing

### Running Tests

Currently, the project doesn't have a comprehensive test suite, but you should:

1. **Manual Testing**
   - Test your changes with both frontend and backend running
   - Verify API endpoints work correctly
   - Test error handling scenarios

2. **Integration Testing**
   - Test GitHub webhook functionality
   - Verify database operations
   - Test LLM integration (if applicable)

### Adding Tests

When adding new features, consider adding:

- Unit tests for utility functions
- Integration tests for API endpoints
- Frontend component tests

## 📝 Submitting Changes

### Commit Message Format

Use clear, descriptive commit messages:

```
feat: add blame analysis caching mechanism
fix: resolve GitHub API rate limiting issue
docs: update installation instructions
refactor: simplify database query logic
```

Prefixes:
- `feat:` - New features
- `fix:` - Bug fixes
- `docs:` - Documentation changes
- `refactor:` - Code refactoring
- `style:` - Code style changes
- `test:` - Adding tests

### Branch Naming

Use descriptive branch names:
- `feature/add-pr-filtering`
- `fix/github-webhook-parsing` 
- `docs/update-api-documentation`

## 🐛 Issue Guidelines

### Reporting Bugs

When reporting bugs, include:

1. **Clear description** of the problem
2. **Steps to reproduce** the issue
3. **Expected vs actual behavior**
4. **Environment details** (OS, Python version, Node version)
5. **Error messages** or logs if available
6. **Screenshots** for UI issues

### Suggesting Features

For feature requests, provide:

1. **Clear description** of the proposed feature
2. **Use case** - why is this feature needed?
3. **Proposed implementation** (if you have ideas)
4. **Alternatives considered**

## 🔄 Pull Request Process

### Before Submitting

1. **Fork the repository** and create your branch from `main`
2. **Make your changes** following the code standards
3. **Format your code** using Black
4. **Test your changes** manually
5. **Update documentation** if needed

### Submitting the PR

1. **Create a pull request** with a clear title and description
2. **Reference related issues** using `Fixes #issue-number`
3. **Describe your changes** and their impact
4. **Include screenshots** for UI changes
5. **List any breaking changes**

### PR Template

```markdown
## Description
Brief description of changes made.

## Type of Change
- [ ] Bug fix
- [ ] New feature  
- [ ] Documentation update
- [ ] Refactoring

## Testing
- [ ] Tested locally
- [ ] API endpoints tested
- [ ] Frontend changes tested

## Screenshots (if applicable)
<!-- Add screenshots for UI changes -->

Fixes #[issue-number]
```

### Review Process

1. **Maintainer review** - code quality, functionality, and standards
2. **Testing verification** - ensure changes work as expected
3. **Documentation check** - verify docs are updated if needed
4. **Approval and merge** - once all checks pass

## 🤔 Questions or Need Help?

- **Check existing issues** for similar questions
- **Create a new issue** for bugs or feature requests
- **Reach out** via email: [rushatgabhane@gmail.com](mailto:rushatgabhane@gmail.com)

## 📄 Code of Conduct

Please be respectful and professional in all interactions. We want to maintain a welcoming environment for all contributors.

## 🎉 Recognition

Contributors will be recognized in:
- Project README acknowledgments
- Release notes for significant contributions
- GitHub contributor listings

Thank you for contributing to BlameGPT! 🚀