# Plan: Provider-agnostic auth — human OIDC login + self-issued machine clients + per-app authz

## Context

Verdikt is becoming an open-source, self-hostable AI-evaluation service that must also run inside the user's company. Two distinct auth needs collided:

- **Humans** (teams viewing eval results) log in via a browser. The repo already has generic OIDC login (commit `6f0a489`), which works against any compliant provider. For this company that provider is **self-hosted GitLab**.
- **Machines** (the eval pipeline / SDK, run from GitLab CI) need non-interactive auth. The SDK currently uses the OAuth2 `client_credentials` grant against the *login* IdP. This broke when the login IdP became Google (`unsupported_grant_type: client_credentials` — Google has no such grant), and would break for any adopter whose IdP lacks it.

**Decision (the architecture that ends the provider-coupling):** decouple the two paths. Human login stays generic OIDC (provider = config). Machine auth stops using the external IdP entirely — **Verdikt becomes its own OAuth2 `client_credentials` issuer**, minting **opaque, DB-backed tokens** (no signing keys, instant revoke). Both humans and machines resolve to one `Principal`, checked against one `app_principals` permission table: admins see all apps, everyone else sees only the apps bound to their email (human) or client_id (machine).

Outcome: `make eval` works regardless of the login provider; per-team machine clients get real identities and per-app permissions; adopters need no special IdP for machines; provider choice is purely deployment env, never code.

The opaque-token choice over self-signed-JWT+JWKS is deliberate: issuer and resource server are the same backend, so JWKS's stateless-verification benefit is unused, while opaque tokens give instant revoke and zero key management. `client_id`+`secret` are stored either way (registry is unavoidable).

---

## Backend conventions to reuse (verified)

- **Tables**: SQLAlchemy Core `sa.Table` in `backend/src/db/tables/*.py`, registered on `sa_metadata` from `backend/src/db/pg.py`. New tables MUST be imported in `backend/src/db/alembic.py` so autogenerate sees them.
- **Migrations**: autogenerate is wired (`backend/alembic/env.py` sets `target_metadata = sa_metadata`). Generate: `cd backend && uv run alembic revision --autogenerate -m "..."`; apply: `make upgrade-db`. File template is date-prefixed.
- **Repositories**: subclass `BaseRepository[Create, Schema, Update]` (`backend/src/repositories/base.py`), `__init__` passes `(table, schema)`; methods take `conn: AsyncConnection` first. Pattern: `backend/src/repositories/apps.py`. Return `schema.model_validate(row._mapping)`.
- **DI**: repos/commands/queries instantiated as module singletons in `backend/src/dependencies.py`; routes inject `conn` via `Depends(get_connection)`.
- **Router**: `/v1` prefix with global guard `dependencies=[Depends(decoded_jwt_token)]` in `backend/src/api/v1/router.py`. Unauthenticated endpoints live at app level in `backend/src/api_app.py` (e.g. `/.well-known`).
- **Commands** raise `ValueError`; routes catch → `HTTPException` (see `post_app_evaluation` in `routes/app.py`).
- **Enums**: `StrEnum` in `backend/src/constants.py`.
- **Config**: `PostgresSettings` / `APISettings` in `backend/src/config.py`.
- **SDK contract** (`../verdikt-sdk-python/verdikt_sdk/auth.py`, `models.py`) — fixed, satisfy it so the SDK needs **zero code change**:
  1. `GET {base_url}/.well-known` → `{ "issuer": X }`
  2. `GET {X}/.well-known/openid-configuration` → `{ "token_endpoint": T }`
  3. `POST T` form `grant_type=client_credentials` + HTTP Basic(client_id, secret) → `{ access_token, token_type, expires_in }`
  4. every call: `Authorization: Bearer {access_token}`

---

## Step 1 — Machine issuer (gets `make eval` working)

**Config** (`backend/src/config.py`, `APISettings`):
- `SERVICE_BASE_URL: str = "http://localhost:8000"` — Verdikt's own URL, advertised as the M2M issuer.
- `MACHINE_TOKEN_TTL: int = 3600`.

**Constants** (`backend/src/constants.py`):
```python
class SubjectType(StrEnum):
    EMAIL = "email"
    CLIENT = "client"
```

**Tables** (`backend/src/db/tables/machine_clients.py`, `machine_tokens.py`; register both in `backend/src/db/alembic.py`):
- `machine_clients`: `id` pk, `client_id` str unique, `client_secret_hash` str, `name` str, `is_admin` bool default false, `revoked` bool default false, `created_at` ts `server_default=func.now()`.
- `machine_tokens`: `id` pk, `token_hash` str unique, `client_id` str FK→`machine_clients.client_id`, `expires_at` ts, `revoked` bool default false, `created_at` ts.

**Schemas** (`backend/src/schemas/machine_client.py`, `machine_token.py`): `*CreateSchema`/`*Schema`/`*UpdateSchema` per convention.

**Repositories** (`backend/src/repositories/machine_client.py`, `machine_token.py`):
- `MachineClientRepository.get_by_client_id(conn, client_id)`.
- `MachineTokenRepository.get_by_hash(conn, token_hash)`, `.revoke_for_client(conn, client_id)`.
- Register singletons in `dependencies.py`.

**Token issuance** (`backend/src/auth/commands.py` — new module, or extend pattern):
- `issue_machine_token(conn, client_id, client_secret) -> (raw_token, ttl)`: look up client; `secrets.compare_digest` the stored hash vs `sha256(secret)`; reject (`ValueError("invalid_client")`) if missing/revoked/mismatch; mint `raw = "vkt_" + secrets.token_urlsafe(32)`; store row with `token_hash=sha256(raw)`, `expires_at=now+ttl`; return `(raw, ttl)`.
- Use `hashlib.sha256(...).hexdigest()` for all hashing.

**Discovery + token endpoints** (`backend/src/api_app.py`, app-level = unauthenticated):
- Repurpose `GET /.well-known` to return `{"issuer": settings.SERVICE_BASE_URL}` (was the GitLab issuer — humans never call this; the frontend talks to GitLab directly).
- Add `GET /.well-known/openid-configuration` → `{"token_endpoint": f"{SERVICE_BASE_URL}/auth/token"}`.
- Add `POST /auth/token`: parse HTTP Basic creds + form `grant_type` (must be `client_credentials`), call `issue_machine_token`, return `{access_token, token_type:"Bearer", expires_in}`; map `ValueError` → `HTTPException(401)`.

**Unified auth dependency** (`backend/src/api/deps.py`): add `authenticate` returning a `Principal` pydantic model `{subject, subject_type, is_admin}`:
- If `token.startswith("vkt_")` → machine path: `sha256` → `machine_tokens.get_by_hash` → validate not revoked/expired → load client → `Principal(client_id, CLIENT, client.is_admin)`.
- Else → human path: existing `token_verifier.decoded_token` (unchanged), `Principal(email, EMAIL, email in admin_emails)`.
- Keep `decoded_jwt_token` until Step 3 swaps the router guard.

**App wiring** (`backend/main.py` `evaluate()` + root `.env`): point SDK at the backend as issuer; `VERDIKT_CLIENT_ID`/`VERDIKT_CLIENT_SECRET` become *Verdikt* credentials (not Google). `VerdiktClient("http://localhost:8000", client_id=..., client_secret=...)` already does the right discovery once issuer=backend.

**Admin CLI** (`backend/main.py`): `create_client(name, app: str|None, admin: bool)` → generate `client_id="mc_"+token_urlsafe(12)`, `secret="secret_"+token_urlsafe(32)`, store client (hash secret); if `app` given, add `app_principals(app_id_of(app), CLIENT, client_id)` (after Step 3); print `client_id` + `secret` once.

**SDK**: no change. Delete plans for any Google service-account path.

---

## Step 2 — GitLab human login (config only)

- In GitLab: create OAuth application — scopes `openid email profile`, redirect `http://localhost:5173/auth/signinwin/oidc`, **Confidential unchecked** (public PKCE).
- Backend `.env`: `OIDC_ISSUER=<gitlab base url>`, `OIDC_AUDIENCE=<application id>`.
- Frontend `frontend/.env`: `VITE_OIDC_ISSUER=<gitlab base url>`, `VITE_OIDC_CLIENT_ID=<application id>`; **remove** `VITE_OIDC_CLIENT_SECRET`.
- Frontend `frontend/src/services/auth.ts`: **remove** the `client_secret` line added for Google (back to pure PKCE).
- No `hd`/domain hardening needed — self-hosted GitLab's user base is the company.

`TokenVerifier` (`backend/src/api/auth.py`) needs no change: GitLab `iss` = its base URL, discovery + JWKS standard.

---

## Step 3 — Per-app authz

**Table** (`backend/src/db/tables/app_principals.py`; register in `alembic.py`):
- `app_principals`: `id` pk, `app_id` int FK→`apps.id` (cascade delete, matching existing FK convention), `subject_type` str, `subject` str, `unique(app_id, subject_type, subject)`.

**Repository** (`backend/src/repositories/app_principal.py`): `app_ids_for(conn, subject_type, subject) -> list[int]`, `add(conn, app_id, subject_type, subject)`. Singleton in `dependencies.py`.

**Authz helper** (`backend/src/auth/queries.py` or `deps.py`):
- `allowed_app_ids(conn, principal) -> list[int] | None` → `None` when `principal.is_admin` (means "all apps"), else the bound ids.
- `require_app_access(app_id, principal=Depends(authenticate))` guard → 403 if `ids is not None and app_id not in ids`.

**Nested-resource resolvers** (critical — most routes are under `/evaluation/{id}` and `/sample/{id}`): add helpers to resolve `evaluation_id`/`sample_id` → owning `app_id` (sample→evaluation→app) before the access check, so a member can't read another team's data by guessing an id. Reuse existing repos (`evaluation_repo`, `sample_repo`).

**Enforcement**:
- Swap router guard in `backend/src/api/v1/router.py`: `Depends(decoded_jwt_token)` → `Depends(authenticate)`.
- List endpoint `get_apps` (`routes/app.py`): filter by `allowed_app_ids` (admin/None → all via `get_many`, else `get_by_many_ids`).
- App-scoped routes (`/app/{app_id}/...`, evaluation/sample routes): add `Depends(require_app_access)` (or inline resolve→check for nested ones).
- Machine principal with `is_admin=True` (central pipeline) → all apps; team client bound to one app → only that app.

**Member admin CLI** (`backend/main.py`): `add_member(app: str, email: str)` → `app_principals.add(..., EMAIL, email)`.

---

## Verification

**Step 1 (machine issuer):**
1. `make upgrade-db` applies the new migration cleanly.
2. `cd backend && uv run main.py` (or `make api`) up. `curl localhost:8000/.well-known` → issuer=backend; `curl localhost:8000/.well-known/openid-configuration` → token_endpoint.
3. `uv run python -c "..."` create a client via the CLI; `curl -u client_id:secret -d grant_type=client_credentials localhost:8000/auth/token` → `access_token` `vkt_...`.
4. `curl -H "Authorization: Bearer vkt_..."` a `/v1` route → 200; bad/expired token → 401.
5. `make eval` runs end-to-end against the backend (the original failing command).
6. Backend tests: `make test` green (add unit tests for `issue_machine_token` valid/invalid/expired and `authenticate` machine vs human branch, per `backend/TESTING.md` — factories, `@pytest.mark.anyio`, AAA).

**Step 2 (login):** `make dev`, open frontend, log in via GitLab → redirected to GitLab, back, authenticated; API calls carry the GitLab id_token and succeed.

**Step 3 (authz):**
1. Admin email (in `ADMIN_EMAILS`) sees all apps; non-admin sees only bound apps; unbound app detail/nested route → 403.
2. Guessing another team's `evaluation_id`/`sample_id` → 403 (nested resolver works).
3. Machine client bound to one app can only write/read that app; `is_admin` client sees all.
4. `make test` green incl. new authz tests (list filter, `require_app_access`, nested resolution).

---

## Out of scope / follow-ups
- GitLab CI **OIDC id_tokens** (secret-less M2M via JWKS federation) — documented upgrade, not built now.
- Tenancy data-model beyond per-app binding (groups-claim mapping from GitLab).
- Self-signed-JWT issuer variant — rejected for this single-backend topology.
- Rotating the secrets already pasted in chat (Google client secret `GOCSPX-…`, etc.) before any production use.
