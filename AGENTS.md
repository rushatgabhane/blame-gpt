# Repository Guidelines

## Project Structure & Module Organization
- Backend (FastAPI, Python 3.13): `controllers/`, `services/`, `libs/`, `middlewares/`, `models/`, entrypoint `main.py`.
- Data & DB: SQLite at `data/cache.db`; SQL migrations in `libs/sqlite/*/migrations/`.
- Frontend (React + TypeScript + Vite): `frontend/` with `src/`, `public/`, `package.json`.
- Notebooks & analysis: `notebooks/`.
- Env config: copy `.env.example` to `.env`.

## Build, Test, and Development Commands
Backend
- Setup: `python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt`
- Run API: `uvicorn main:app --reload`
- Migrations: `./migrate.sh`
- Lint: `ruff check` | Format: `ruff format` | Types: `mypy`

Frontend
- Dev server: `cd frontend && npm run dev`
- Build: `cd frontend && npm run build` | Lint: `npm run lint` | Preview: `npm run preview`

## Coding Style & Naming Conventions
- Python: 4‑space indent, line length 120 (`ruff`). Use type hints; keep functions small with early returns. Names: `snake_case` for files/functions, `PascalCase` for classes, `UPPER_SNAKE_CASE` for constants.
- Type checking: `mypy` (py313). Avoid missing types in new code.
- Imports at top; prefer explicit, sorted (ruff fixes with `ruff format`).
- TypeScript/React: follow ESLint defaults in `frontend/`; 2‑space indent; component files `PascalCase.tsx`.

## Testing Guidelines
- No formal test suite yet. When adding tests:
  - Python: use `pytest`, place in `tests/` as `test_*.py`; unit‑test `services/`, integration‑test `controllers/` with FastAPI `TestClient`.
  - Aim for meaningful coverage on core flows (blame pipeline, code review).
  - Run with `pytest -q` once added.

## Commit & Pull Request Guidelines
- Commits: imperative, present tense; concise subject (<=72 chars). Example: `feat(services): rank PRs by cosine similarity`.
- PRs: clear description, link issues (`Closes #123`), include screenshots for frontend UI changes, note DB migrations if any.
- Required checks: `ruff check`, `ruff format`, `mypy`, app runs locally, migrations applied.

## Security & Configuration Tips
- Do NOT set `ENVIRONMENT=production` locally; it may post to live GitHub.
- Keep secrets in `.env` (`GITHUB_TOKEN`, `OPENAI_API_KEY`, `INTERNAL_AUTH_TOKEN`); never commit them.
- Large data stays under `data/`; review notebooks before committing.
