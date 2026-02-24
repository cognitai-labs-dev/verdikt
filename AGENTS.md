# AGENTS.md

AI evaluation service: decouples evaluation/judging from the app being evaluated.
Supports human and LLM-based judgment of Q&A pairs with cost tracking.

## Repository Structure

```
evaluation-app/
├── backend/          # Python FastAPI service
│   ├── src/
│   │   ├── api/v1/routes/    # Thin FastAPI endpoints
│   │   ├── repositories/     # Data access (SQLAlchemy Core)
│   │   ├── */commands.py     # Write/mutation business logic
│   │   ├── */queries.py      # Read/aggregation logic
│   │   ├── schemas/          # Pydantic models
│   │   ├── processors/       # Background workers
│   │   ├── constants.py      # Shared enums
│   │   └── config.py         # pydantic-settings, loaded from .env
│   └── tests/
│       ├── unit/             # No DB required
│       ├── integration/      # Real DB, per-test rollback
│       ├── factories/        # Test data builders
│       └── conftest.py       # db_engine, db_conn fixtures
└── frontend/         # Vue 3 + TypeScript SPA
    └── src/
        ├── api/
        │   ├── fetcher.ts    # Custom fetch wrapper (auth, base URL)
        │   └── generated.ts  # Orval-generated — do NOT edit manually
        ├── components/       # Reusable Vue components (PascalCase)
        ├── views/            # Route-level pages (*View.vue)
        ├── stores/           # use* composables with shared state
        └── utils/format.ts   # Date, cost, percentage formatting
```

---

## Build / Lint / Test Commands

### Backend (run from repo root or `backend/`)

```bash
# Tests
make test                                    # run all tests
make test TA="-v tests/unit/"               # unit tests only
make test TA="-v tests/integration/"        # integration tests only
make test TA="-v tests/path/to/test_file.py::test_function_name"  # single test

# Or directly with uv (from backend/)
uv run pytest -v tests/
uv run pytest tests/unit/judgement/test_judgement_queries.py::test_pass_count_for_llm_only

# Linting & formatting
make ruff-lint      # ruff check --fix src/
make ruff-format    # ruff format src/
make mypy           # mypy src/
make lint           # run all pre-commit hooks

# Server
make api            # start FastAPI (brings up DB + runs migrations first)
make upgrade-db     # run Alembic migrations only
make judge          # start LLM judgment background worker
```

### Frontend (run from `frontend/`)

```bash
pnpm dev            # start dev server
pnpm build          # type-check + production build
pnpm type-check     # vue-tsc --build only
pnpm test:unit      # run all Vitest tests
pnpm test:unit --reporter=verbose path/to/__tests__/MyComponent.spec.ts  # single test file
pnpm lint           # eslint_d --fix --cache (fast, uses daemon)
pnpm lint:ci        # eslint (no daemon, for CI)
pnpm format         # prettier --write src/
pnpm format:ci      # prettier --check src/
pnpm api:generate   # regenerate src/api/generated.ts from OpenAPI spec
```

---

## Backend Code Style (Python)

**Stack:** Python 3.13, FastAPI, SQLAlchemy 2.0 (async Core), Pydantic v2, Alembic, `uv`.

### Formatting
- Ruff formatter + linter; line length **70 characters**
- Ruff rules enforced on `src/`; mypy for type checking

### Types & Naming
- All functions are `async`; no sync DB calls
- Use `StrEnum` for domain enums (see `src/constants.py`)
- Schema naming: `*CreateSchema` / `*Schema` / `*UpdateSchema` (Pydantic)
- `snake_case` for everything; module names are singular nouns

### Architecture Pattern
```
Routes (thin) → Commands/Queries (business logic) → Repositories (DB only)
```
- Routes: validate input, call commands/queries, raise `HTTPException` for errors
- Commands (`commands.py`): mutation logic; raise `ValueError` for domain errors
- Queries (`queries.py`): read/aggregation, pure logic (often no DB needed)
- Repositories: extend `BaseRepository`; use SQLAlchemy Core (`insert`/`select`/`update`/`delete`); return validated Pydantic schemas via `model_validate(row._mapping)`

### Imports
```python
# stdlib first, then third-party, then local — ruff enforces this
from datetime import datetime
from pydantic import BaseModel, Field
from src.constants import JudgmentType
```

### Error Handling
- Domain errors: raise `ValueError` in commands, caught at route level
- HTTP errors: raise `HTTPException(status_code=404, detail="...")` in routes
- Logging: `logging.getLogger(__name__)` per module

### Database
- Tables in `src/db/tables/`; async `psycopg` driver
- Dependency injection: `Depends(get_connection)` in route signatures
- New tables require an Alembic migration in `alembic/versions/`

---

## Frontend Code Style (TypeScript / Vue)

**Stack:** Vue 3, TypeScript ~5.9, Vite 7, Vuetify 3, Vue Router 4, pnpm.

### Formatting
- Prettier: **no semicolons**, **double quotes**, **100-char print width**
- ESLint flat config: Vue essential rules + TypeScript recommended + Vitest plugin

### TypeScript
- `strict` mode via `@vue/tsconfig`
- Type imports: `import type { Foo }` when importing only types
- Generated API types live in `src/api/generated.ts` — import from there, never redefine
- Naming: `*Schema` for API model types, `*Request`/`*Response` for custom payloads

### Vue Components
- Always `<script setup lang="ts">` with Composition API
- Props: `defineProps<{ foo: string; bar: number }>()` (generic syntax)
- Emits: `defineEmits<{ saved: [item: FooSchema] }>()`
- Component files: `PascalCase.vue`; route-level views: `*View.vue`
- `@` alias resolves to `./src/`

### Imports Order (enforced by ESLint)
```ts
// 1. Node built-ins
import { ref } from "node:url"
// 2. External packages
import { ref, computed, onMounted } from "vue"
// 3. Internal — absolute (@/) before relative
import { getApp } from "@/api/generated"
import MyComponent from "@/components/MyComponent.vue"
```

### Patterns
- Data fetching: `async/await` in `onMounted()` with local `ref()` state
- No global store — use component-local state; shared state via simple composables in `src/stores/use*.ts`
- Loading/empty states: `v-progress-linear` + `v-if` guards
- Do **not** manually edit `src/api/generated.ts` — run `pnpm api:generate`

---

## Testing Guidelines

### Backend

Full guidelines: [`backend/TESTING.md`](backend/TESTING.md)

- **No test classes** — plain `async` functions only
- Mark async tests: `@pytest.mark.anyio`
- **Descriptive names**: `test_<method>_<scenario>_<expected_outcome>`
- **Arrange / Act / Assert** sections with comment headers
- **Parametrize** with named IDs: `pytest.param(..., id="descriptive_id")`
- **Factories** in `tests/factories/` for all schema/DB object creation
- **Unit tests** (`tests/unit/`): no DB, pure logic
- **Integration tests** (`tests/integration/`): use `db_conn` fixture (real PG, per-test rollback via `db_engine`)
- **Mock only** external services (LLM APIs, external HTTP); never mock the DB
- Hardcode plain values in tests; do not reuse production constants
- No logic (loops, conditionals) inside tests — if needed, split into separate cases

```python
# Single test example
uv run pytest -v tests/unit/judgement/test_judgement_queries.py::test_pass_count_for_llm_only
```

### Frontend

- Vitest + jsdom + `@vue/test-utils`
- Test files in `src/**/__tests__/` (e.g. `src/components/__tests__/MyComponent.spec.ts`)
- Run a single test file: `pnpm test:unit MyComponent.spec.ts`
- Follow the same Arrange/Act/Assert discipline as the backend
