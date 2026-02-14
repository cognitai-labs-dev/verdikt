# Evaluation App

Standalone AI evaluation service that decouples evaluation and judging from the application being evaluated. Supports human and LLM-based judgment of Q&A pairs with cost tracking and judge calibration.

## Structure

- `backend/` — FastAPI REST API, LLM judge worker, PostgreSQL storage
- `frontend/` — Vue 3 SPA for human judging and viewing results

## Quick Start

```shell
make api      # start DB + migrations + API server
make init     # seed with mock data
make judge    # run LLM judgment worker
make fe       # start frontend dev server
```

## Testing

```shell
make test     # backend tests
make lint     # pre-commit hooks (backend + frontend)
```
