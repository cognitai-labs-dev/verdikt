# AGENTS.md

AI evaluation service: decouples evaluation/judging from the app being evaluated.
Supports human and LLM-based judgment of Q&A pairs with cost tracking.

---

## Backend Architecture

```
Routes (thin) → Commands/Queries (business logic) → Repositories (DB only)
```

- **Routes**: validate input, call commands/queries, raise `HTTPException` for errors
- **Commands** (`commands.py`): mutation logic; raise `ValueError` for domain errors
- **Queries** (`queries.py`): read/aggregation, pure logic (often no DB needed)
- **Repositories**: extend `BaseRepository`; use SQLAlchemy Core; return validated Pydantic schemas via `model_validate(row._mapping)`

### Naming
- Schema naming: `*CreateSchema` / `*Schema` / `*UpdateSchema`
- Module names are singular nouns
- Use `StrEnum` for domain enums (see `src/constants.py`)

### Error Handling
- Domain errors: raise `ValueError` in commands, caught at route level
- HTTP errors: raise `HTTPException(status_code=404, detail="...")` in routes

### Database
- New tables require an Alembic migration in `alembic/versions/`

### Auth & Authorization
- Two auth paths, one `Principal`. **Humans**: generic OIDC id_token (provider = `OIDC_ISSUER`), verified by `TokenVerifier` (`src/api/auth.py`). **Machines**: Verdikt is its own `client_credentials` issuer — opaque `vkt_` tokens (`src/auth/`, `machine_clients`/`machine_tokens` tables); discovery + `/auth/token` live app-level in `src/api_app.py`.
- `authenticate` (`src/api/deps.py`) resolves either token type to a `Principal{subject, subject_type, is_admin}`; it's the global `/v1` router guard.
- Per-app authz via `app_principals` (email/client → app). Admins (the access-config `admins:` list) see all. Guard app-scoped routes with `require_app_access`; nested routes with `require_evaluation_access` / `require_sample_access` (resolve id → owning app before the check).
- Account/permission management (no CLI): **machine clients** are app-scoped and self-service — any principal with access to an app manages that app's clients via `/v1/app/{app_id}/machine-clients` (gated by `require_app_access`; created clients are non-admin and bound only to that app). There is no separate admin machine-client API. **Email principals + admins** declaratively via the access-config YAML (`ACCESS_CONFIG_PATH`, `src/auth/access_config.py`), reconciled into `app_principals` on startup; admins are the only global role (they see every app).

---

## Frontend Patterns

- Data fetching: `async/await` in `onMounted()` with local `ref()` state
- No global store — component-local state; shared state via composables in `src/stores/use*.ts`
- Loading/empty states: `v-progress-linear` + `v-if` guards
- Do **not** manually edit `src/api/generated.ts` — run `pnpm api:generate`
- Naming: `*Schema` for API model types, `*Request`/`*Response` for custom payloads

---

## Testing Conventions

Full backend guidelines: [`backend/TESTING.md`](backend/TESTING.md)

### Backend
- **No test classes** — plain `async` functions only
- Mark async tests: `@pytest.mark.anyio`
- **Descriptive names**: `test_<method>_<scenario>_<expected_outcome>`
- **Arrange / Act / Assert** sections with comment headers
- **Parametrize** with named IDs: `pytest.param(..., id="descriptive_id")`
- Use **factories** in `tests/factories/` for all schema/DB object creation
- **Mock only** external services (LLM APIs, external HTTP); never mock the DB
- Hardcode plain values in tests; do not reuse production constants
- No logic (loops, conditionals) inside tests — split into separate cases instead

### Frontend
- Follow the same Arrange/Act/Assert discipline as the backend
