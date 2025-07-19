# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

BlameGPT is a FastAPI-based AI tool that helps workflows of engineers that use github. It uses Python 3.13 and has a React TypeScript frontend.

## Development Commands

### Backend (Python FastAPI)
- Start development server: `uvicorn main:app --reload`
- Run linting: `ruff check`
- Run type checking: `mypy`
- Format code: `ruff format`
- Run database migrations: `./migrate.sh`
- Run notebooks: `jupyter lab`

### Frontend (React TypeScript)
- Start development server: `cd frontend && npm run dev`
- Build production: `cd frontend && npm run build`
- Run linting: `cd frontend && npm run lint`
- Preview build: `cd frontend && npm run preview`

## Architecture

### Backend Structure
```
blame-gpt/
├── main.py              # FastAPI application entry point with lifespan management
├── controllers/         # FastAPI route handlers
│   ├── blame_controller.py      # Main blame detection endpoint
│   ├── issue_controller.py      # Issue processing
│   ├── test_steps_controller.py # Test step generation
│   ├── docs_controller.py       # Documentation endpoints
│   ├── user_controller.py       # User management and usage tracking
│   └── _deprecated_deploy_blocker_controller.py # Deprecated functionality
├── services/            # Business logic layer
│   ├── blame_pipeline.py        # Core blame detection pipeline
│   ├── user_service.py          # User management and usage tracking
│   ├── github/                  # GitHub API integrations
│   │   ├── issue_service.py
│   │   ├── pull_request_service.py
│   │   ├── notification_service.py
│   │   └── comment_service.py
│   ├── docs_service/           # Documentation indexing and retrieval
│   │   ├── sync.py             # Documentation synchronization
│   │   ├── graph.py            # Document graph processing
│   │   ├── nodes.py            # Document node definitions
│   │   └── run_graph.py        # Graph execution
│   ├── test_step/              # Test step generation and management
│   │   ├── test_step_pipeline.py
│   │   ├── test_ingestion.py
│   │   └── qa_tests.csv
│   └── _deprecated_historical_deploy_blocker_pipeline.py # Deprecated functionality
├── libs/                # Shared libraries and utilities
│   ├── github.py               # GitHub API client
│   ├── llm.py                  # LLM abstractions
│   ├── helpers.py              # General utility functions
│   ├── constants.py            # Application constants
│   ├── prompt_templates/       # LLM prompt templates
│   │   ├── code_diff_summary.py
│   │   ├── command_classification.py
│   │   ├── consolidate_test_steps.py
│   │   ├── culprit_pull_request_with_score.py
│   │   ├── doc_edit_evaluation.py
│   │   ├── doc_edit_suggestion.py
│   │   ├── issue_test_steps_for_bug.py
│   │   ├── pull_request_intent.py
│   │   └── pull_request_test_steps.py
│   └── sqlite/                # Database clients and migrations
│       ├── core/              # Core application database
│       │   ├── core_sqlite_client.py
│       │   ├── core_queries.py
│       │   └── migrations/
│       └── docs/              # Documentation database
│           ├── docs_sqlite_client.py
│           ├── docs_queries.py
│           └── migrations/
├── models/              # Pydantic data models
│   ├── models.py              # Core data models
│   └── enums.py               # Enumeration definitions
├── middlewares/         # FastAPI middleware
│   └── auth_middleware.py     # Authentication middleware
├── notebooks/           # Jupyter notebooks for analysis
│   ├── deploy_blocker.ipynb
│   ├── index_repo.ipynb
│   └── treesitter.ipynb
├── data/                # Large dataset files
│   ├── app/             # Expensify app data for analysis
│   ├── cache.db         # SQLite cache database
│   └── docs.db          # SQLite documentation database
├── deploy.sh            # Deployment script
├── migrate.sh           # Database migration script
├── requirements.txt     # Python dependencies
└── pyproject.toml       # Python project configuration
```

### Key Components

**Blame Pipeline (`services/blame_pipeline.py`)**: The core algorithm that analyzes issues and finds culprit PRs using:
- Embedding-based similarity search between issues and PRs
- LLM-powered ranking of potential culprit PRs
- Streams results back to GitHub Actions

**Database Management**: Uses SQLite with custom migration system:
- `libs/sqlite/core/` - Main application data (issues, PRs, embeddings, users, usage tracking)
- `libs/sqlite/docs/` - Documentation indexing for Q&A features
- Migrations auto-apply on startup and can be run manually with `./migrate.sh`
- Database files stored in `data/` directory: `cache.db` and `docs.db`

**GitHub Integration**: Comprehensive GitHub API integration for:
- Issue and PR retrieval
- Comment posting and management
- Webhook handling
- Notification processing and polling
- User authentication and management

**LLM Integration**: Centralized LLM handling with:
- Prompt templates in `libs/prompt_templates/` for various use cases
- Usage tracking and cost calculation
- Support for multiple LLM models with pricing information
- Token counting and cost optimization

### Environment Setup

1. Use Python 3.13
2. Create virtual environment: `python3 -m venv venv`
3. Activate: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Copy environment file: `cp .env.example .env`
6. Set GitHub token and OpenAI API key in `.env`

Store embedding as blob

### Key Workflows

**Issue Processing**: When GitHub Action triggers `/api/blame`:
1. User authentication and usage tracking
2. Issue converted to embedding
3. Recent PRs retrieved and embedded
4. Cosine similarity ranking
5. Top PRs analyzed by LLM for culprit detection
6. Results posted as GitHub comment
7. Usage and cost tracking stored in database

**Documentation Sync**: Automated sync of documentation for Q&A features:
- Scheduled daily sync at 8 AM via cron job
- Graph-based document processing and indexing
- Real-time document updates and retrieval

**Database Migrations**: Pure SQL migrations in `libs/sqlite/[db_name]/migrations/` with naming pattern `000001_description.sql`

**User Management**: Comprehensive user tracking system:
- User registration and authentication
- Usage logging for all API calls
- Cost tracking per user and command
- Admin endpoints for user management

**Test Generation**: Automated test step generation:
- QA test ingestion from CSV files
- Test step pipeline for bug analysis
- Integration with PR and issue workflows

**Notification System**: Real-time GitHub notification processing:
- Polls GitHub notifications every 5 seconds
- Processes issues, PRs, and comments
- Automated responses and analysis

## Frontend

React TypeScript application built with Vite, located in `frontend/` directory:
- Modern React with TypeScript
- Vite for fast development and building
- ESLint configuration for code quality
- Responsive design with video backgrounds
- Development server on port 5173

## Key Features

### AI-Powered Blame Detection
- Embedding-based similarity matching between issues and PRs
- LLM-powered analysis for identifying culprit PRs
- Contextual understanding of code changes and their impact

### User Management & Analytics
- GitHub-based user authentication
- Usage tracking for all API endpoints
- Cost calculation and monitoring
- Admin dashboard for user management

### Documentation Intelligence
- Automated documentation indexing and synchronization
- Graph-based document processing
- Real-time Q&A capabilities

### Test Generation
- Automated test step generation for bugs
- Integration with existing QA workflows
- Test consolidation and optimization

### GitHub Integration
- Real-time notification processing
- Automated comment posting
- Webhook handling for various GitHub events
- Multi-repository support

## Database Schema

### Core Database (`cache.db`)
- **users**: User profiles and authentication data
- **usage_logs**: API usage tracking per user
- **llm_calls**: LLM usage and cost tracking
- **issues**: GitHub issue metadata and embeddings
- **pull_requests**: PR data and embeddings
- **test_steps**: Generated test steps for PRs
- **test_suites**: Test suite organization

### Documentation Database (`docs.db`)
- **documents**: Indexed documentation content
- **embeddings**: Document embeddings for similarity search
- **document_graphs**: Relationship mapping between documents

## Configuration

### Environment Variables
- `GITHUB_TOKEN`: GitHub API authentication
- `OPENAI_API_KEY`: OpenAI API access
- `ENVIRONMENT`: Deployment environment (development/production)
- `INTERNAL_AUTH_TOKEN`: Internal API authentication

### Database Paths
- Core database: `data/cache.db`
- Documentation database: `data/docs.db`

## Deployment

- Use `deploy.sh` for deployment
- Ensure all environment variables are set
- Database migrations run automatically on startup
- Production environment enables additional features like test ingestion