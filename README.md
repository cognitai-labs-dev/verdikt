# Verdikt

Standalone AI evaluation service that decouples evaluation and judging from the application being evaluated. Supports human and LLM-based judgment of Q&A pairs with cost tracking and judge calibration.

## Structure

- `backend/` — FastAPI REST API, LLM judge worker, PostgreSQL storage
- `frontend/` — Vue 3 SPA for human judging and viewing results

## Authentication

Verdikt has **two independent auth paths** — one for humans, one for machines —
that both resolve to a single `Principal` checked against one per-app permission
table (see [Authorization](#authorization-per-app-access)).

- **Humans** log in via any **OIDC-compliant** provider — GitLab, Google
  Workspace, Zitadel, Keycloak, Authentik, Okta, Azure AD, etc. Pick one per
  deployment via env. The frontend runs authorization-code + PKCE and sends the
  **id_token** to the backend, which verifies it against the issuer's JWKS.
- **Machines** (the eval pipeline / SDK) authenticate against **Verdikt itself**,
  not the login IdP. Verdikt is its own OAuth2 `client_credentials` issuer,
  minting opaque, DB-backed `vkt_` tokens (instant revoke, no key management).
  This is why `make eval` works regardless of which login provider you pick.
  See [SDK access](#sdk-access-machine-clients).

### 1. Create an OAuth client in your IdP

Create a **Web / SPA application with PKCE** and register:

- **Redirect URI**: `{origin}/auth/signinwin/oidc`
  (e.g. `http://localhost:5173/auth/signinwin/oidc`).
  Path is `{origin}/auth/signinwin/{authName}` with `authName = "oidc"`; adjust
  for your port/domain.
- **Post-logout redirect URI**: `{origin}/` (e.g. `http://localhost:5173/`).

### 2. Frontend config

Copy `frontend/.env.example` to `frontend/.env`:

```
# GitLab (self-hosted or gitlab.com)
VITE_OIDC_ISSUER=https://gitlab.example.com
VITE_OIDC_CLIENT_ID=<application-id>

# Google
VITE_OIDC_ISSUER=https://accounts.google.com
VITE_OIDC_CLIENT_ID=<your-client-id>

# Zitadel
VITE_OIDC_ISSUER=https://<your-instance>.zitadel.cloud
VITE_OIDC_CLIENT_ID=<your-client-id>
```

> **GitLab**: create the OAuth application with scopes `openid email profile`,
> redirect `{origin}/auth/signinwin/oidc`, and **Confidential unchecked** (public
> PKCE — the SPA holds no secret). The **Application ID** is your client id; the
> issuer is the GitLab base URL.

### 3. Backend config

Copy `.env.example` to `.env`:

```
OIDC_ISSUER=http://localhost:8080   # must match the token's `iss`
OIDC_AUDIENCE=<spa-client-id>        # the frontend token's `aud` (comma-separated list)
```

`OIDC_AUDIENCE` lists only **human** (frontend SPA) client ids — machine clients
do not use OIDC, so they are not listed here. The JWKS URI is auto-discovered
from the issuer's `/.well-known/openid-configuration`. Set `OIDC_JWKS_URI` only
to pin it explicitly.

After login the IdP redirects to the redirect URI; the app exchanges the code
for tokens and continues to the original destination (or `/`). Logout redirects
back to `/`.

### Local dev with Zitadel

The `docker-compose.yaml` ships a self-hosted Zitadel (console on `:8080`,
login UI on `:3000`) so you can develop without an external IdP.

1. Start the stack (db + zitadel + login):

   ```shell
   make up-d        # docker compose up -d
   ```

   Wait until the `verdikt-zitadel` container is healthy (~30s on first run).

2. Open the console at <http://localhost:8080/ui/console> and log in as the
   default instance admin:

   ```
   zitadel-admin@zitadel.localhost
   Password1!
   ```

3. Create (or reuse) a **Project**, then add an **Application**:
   - Use: **User Agent** → **PKCE**.
   - Enable **Dev Mode** on the app (allows the `http://` redirect below).
   - **Redirect URI**: `http://localhost:5173/auth/signinwin/oidc`
   - **Post-logout redirect URI**: `http://localhost:5173/`

4. Copy the application's **Client ID**, then fill the env files:

   `frontend/.env`:

   ```
   VITE_OIDC_ISSUER=http://localhost:8080
   VITE_OIDC_CLIENT_ID=<client-id>
   ```

   root `.env`:

   ```
   OIDC_ISSUER=http://localhost:8080
   OIDC_AUDIENCE=<client-id>        # the SPA client id (machines don't use OIDC)
   ```

5. Run the app and log in:

   ```shell
   make dev         # db + migrations + backend + frontend
   ```

   The frontend is served at <http://localhost:5173>; an unauthenticated route
   redirects to the Zitadel login.

### SDK access (machine clients)

Machine auth is handled **entirely by Verdikt** — there is no IdP service user.
Verdikt exposes the standard `client_credentials` discovery + token endpoints
(`/.well-known`, `/.well-known/openid-configuration`, `POST /auth/token`) and
mints opaque `vkt_` tokens. The SDK needs no special configuration beyond the
backend URL and a client id/secret.

1. Mint a client with the admin CLI (it prints the secret **once**):

   ```shell
   cd backend
   # central pipeline that may touch every app:
   uv run main.py create-client "ci-pipeline" --admin
   # team client scoped to a single app:
   uv run main.py create-client "team-a" --app <app-slug>
   ```

2. Paste the printed credentials into root `.env`:

   ```
   VERDIKT_CLIENT_ID=mc_xxxxxxxx
   VERDIKT_CLIENT_SECRET=secret_xxxxxxxx
   SERVICE_BASE_URL=http://localhost:8000   # Verdikt's own URL = the M2M issuer
   ```

   `make eval` (and any SDK consumer) now authenticates against Verdikt. Restart
   the backend after changing `.env` (it reads it at startup).

To revoke a client, set `revoked=true` on its `machine_clients` row; live tokens
expire after `MACHINE_TOKEN_TTL` seconds.

## Authorization (per-app access)

Both humans and machines resolve to one `Principal` checked against the
`app_principals` table:

- **Admins see every app.** Humans whose `email` is in `ADMIN_EMAILS`; machine
  clients created with `--admin`.
- **Everyone else sees only the apps they are bound to** — matched by email
  (human) or `client_id` (machine). Unbound app / evaluation / sample routes
  return `403`; nested ids (`/evaluation/{id}`, `/sample/{id}`) are resolved to
  their owning app first, so guessing another team's id is also `403`.

Bind principals with the CLI:

```shell
cd backend
uv run main.py add-member <app-slug> alice@example.com   # bind a human to an app
uv run main.py create-client "team-a" --app <app-slug>   # bind a new machine client
```

Set the admin allowlist in root `.env`:

```
ADMIN_EMAILS=admin@example.com,lead@example.com
```

## Deployment

Verdikt ships as two prebuilt Docker images on GHCR, built by CI on every
`master` push (`latest` + `sha-…`) and on `v*` tags (semver tags):

- `ghcr.io/<owner>/evaluation-app/frontend`
- `ghcr.io/<owner>/evaluation-app/backend`

### Frontend is configured at runtime, not build time

Vite normally inlines `VITE_*` at build time, which would mean one image per
deployment. Instead the frontend reads its config at **runtime** from
`window.__APP_CONFIG__` (served as `/config.js`). The container entrypoint
substitutes that file from env vars on startup (`envsubst`), so **the same
image works against any IdP** — no rebuild, no per-customer artifact.

Run it with the three config vars:

```shell
docker run -p 3000:3000 \
  -e API_URL=https://verdikt-api.your-domain \
  -e OIDC_ISSUER=https://accounts.google.com \
  -e OIDC_CLIENT_ID=<your-client-id> \
  ghcr.io/<owner>/evaluation-app/frontend:latest
```

| Var             | Purpose                                  |
| --------------- | ---------------------------------------- |
| `API_URL`       | Base URL of the backend API the SPA calls |
| `OIDC_ISSUER`   | Your IdP issuer (Google, Zitadel, …)      |
| `OIDC_CLIENT_ID`| The SPA's OAuth client id                 |

The backend reads its config from env/`.env` at startup already (see
[Backend config](#3-backend-config)), so it's reconfigured the same way — set
`OIDC_ISSUER`, `OIDC_AUDIENCE`, `ADMIN_EMAILS`, `SERVICE_BASE_URL`, and
`APP_DB_*` on the container. `SERVICE_BASE_URL` must be the backend's public URL
(it's advertised to SDK clients as the machine-token issuer).

> Local dev does **not** use these images — `make dev` runs the Vite dev server
> and reads `frontend/.env` via `import.meta.env` (the `${…}` tokens in
> `config.js` are detected and ignored in dev).

## Quick Start

```shell
make dev # start DB + migrations + API server + FE
make eval # seed with mock data
make judge    # run LLM judgment worker
```

## Testing

```shell
make test     # backend tests
make lint     # pre-commit hooks (backend + frontend)
```
