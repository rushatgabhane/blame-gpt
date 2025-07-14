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
│   └── docs_controller.py       # Documentation endpoints
├── services/            # Business logic layer
│   ├── blame_pipeline.py        # Core blame detection pipeline
│   ├── github/                  # GitHub API integrations
│   │   ├── issue_service.py
│   │   ├── pull_request_service.py
│   │   └── notification_service.py
│   ├── docs_service/           # Documentation indexing and retrieval
│   └── test_generation/        # Test step generation
├── libs/                # Shared libraries and utilities
│   ├── github.py               # GitHub API client
│   ├── llm.py                  # LLM abstractions
│   ├── prompt_templates/       # LLM prompt templates
│   └── sqlite/                # Database clients and migrations
│       ├── core/              # Core application database
│       └── docs/              # Documentation database
├── models/              # Pydantic data models
└── middlewares/         # FastAPI middleware
```

### Key Components

**Blame Pipeline (`services/blame_pipeline.py`)**: The core algorithm that analyzes issues and finds culprit PRs using:
- Embedding-based similarity search between issues and PRs
- LLM-powered ranking of potential culprit PRs
- Streams results back to GitHub Actions

**Database Management**: Uses SQLite with yoyo-migrations for schema management:
- `libs/sqlite/core/` - Main application data (issues, PRs, embeddings)
- `libs/sqlite/docs/` - Documentation indexing for Q&A features
- Migrations auto-apply on startup and can be run manually with `./migrate.sh`

**GitHub Integration**: Comprehensive GitHub API integration for:
- Issue and PR retrieval
- Comment posting
- Webhook handling
- Notification processing

**LLM Integration**: Centralized LLM handling with prompt templates in `libs/prompt_templates/`

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
1. Issue converted to embedding
2. Recent PRs retrieved and embedded
3. Cosine similarity ranking
4. Top PRs analyzed by LLM for culprit detection
5. Results posted as GitHub comment

**Documentation Sync**: Automated sync of documentation for Q&A features via scheduled jobs

**Database Migrations**: Pure SQL migrations in `libs/sqlite/[db_name]/migrations/` with naming pattern `000001_description.sql`

## Frontend

React TypeScript application built with Vite, located in `frontend/` directory.