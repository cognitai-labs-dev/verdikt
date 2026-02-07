# Claude Code Guidelines

## Project Overview

AI evaluation service that decouples evaluation/judging from the app being evaluated. Supports human and LLM-based judgment of Q&A pairs with cost tracking.

## Tech Stack

- Python 3.13, FastAPI, SQLAlchemy 2.0 (async, Core), PostgreSQL
- Pydantic for schemas, Alembic for migrations
- `uv` as package manager, Typer for CLI
- LLM integration via `instructor`, `litellm`, `yalc`

## Commands

- `uv run pytest` - run tests (`make test TA="-v tests/"`)
- `make api` - start FastAPI server (runs DB + migrations first)
- `make judge` - start LLM judgment worker
- `make upgrade-db` - run Alembic migrations
- `make ruff-lint` - lint with ruff
- `make ruff-format` - format with ruff
- `make mypy` - type check
- `make lint` - run all pre-commit hooks

## Architecture

```
API Routes → Commands/Queries → Repositories → Database
```

- **Repositories** (`src/repositories/`) - data access only (SQLAlchemy Core), extend `BaseRepository`
- **Commands** (`src/*/commands.py`) - write/mutation business logic
- **Queries** (`src/*/queries.py`) - read/aggregation logic
- **Schemas** (`src/schemas/`) - Pydantic models with separate `*CreateSchema`, `*Schema`, `*UpdateSchema`
- **Routes** (`src/api/v1/routes/`) - FastAPI endpoints, thin layer delegating to commands/queries
- **Processors** (`src/processors/`) - background workers (e.g. LLM judgment processor)

## Database

- Tables defined in `src/db/tables/` (apps, evaluations, samples, judgments, app_datasets)
- Migrations in `alembic/versions/`
- Local DB: PostgreSQL via docker-compose on port 5433
- Async engine throughout (`psycopg` driver)

## Key Conventions

- Ruff line length: **70 characters**
- Pure async code everywhere
- No test classes - use plain test functions
- Dependency injection via `src/dependencies.py`
- Enums in `src/constants.py` (JudgmentType, JudgmentStatus, EvaluationType)
- Config via pydantic-settings in `src/config.py`, loaded from `.env`

## Testing

Follow [TESTING.md](TESTING.md) guidelines. Key points:

- Run: `uv run pytest`
- Tests live in `tests/unit/` (no DB) and `tests/integration/` (with DB)
- Factories in `tests/factories/` for creating test data
- Fixtures in `tests/conftest.py` (`db_engine`, `db_conn` with per-test rollback)
- Use Arrange/Act/Assert, descriptive names, parametrize with IDs
- No test classes, no logic in tests, mock only external dependencies
