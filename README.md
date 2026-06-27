# Verdikt

Standalone AI evaluation service that decouples evaluation and judging from the application being evaluated. Supports human and LLM-based judgment of Q&A pairs with cost tracking and judge calibration.

## Structure

- `backend/` — FastAPI REST API, LLM judge worker, PostgreSQL storage
- `frontend/` — Nuxt 4 app (SPA mode) with a Nitro **BFF** for human judging and viewing results

## Authentication

Verdikt has **two independent auth paths** — one for humans, one for machines —
that both resolve to a single `Principal` checked against one per-app permission
table (see [Authorization](#authorization-per-app-access)).

- **Humans** log in via any **OIDC-compliant** provider — GitLab, Google
  Workspace, Zitadel, Keycloak, Authentik, Okta, Azure AD, etc. Pick one per
  deployment via env. The **frontend BFF** (Nuxt/Nitro server) runs the
  authorization-code + PKCE flow server-side, keeps the tokens in an `httpOnly`
  session cookie, and forwards the **id_token** to the backend (verified against
  the issuer's JWKS) — the browser never holds a token.
- **Machines** (the eval pipeline / SDK) authenticate against **Verdikt itself**,
  not the login IdP. Verdikt is its own OAuth2 `client_credentials` issuer,
  minting opaque, DB-backed `vkt_` tokens (instant revoke, no key management).
  This is why `make eval` works regardless of which login provider you pick.
  See [SDK access](#sdk-access-machine-clients).

### 1. Create an OAuth client in your IdP

Create a **confidential web application** (the BFF holds the secret) and register:

- **Redirect URI**: `{origin}/auth/callback` (e.g. `http://localhost:3000/auth/callback`).
- **Post-logout redirect URI**: `{origin}/` (e.g. `http://localhost:3000/`).
- **Scopes**: `openid email profile`.

### 2. Frontend (BFF) config

Copy `frontend/.env.example` to `frontend/.env`. Login is server-side, so these
are `NUXT_*` (read by the Nitro server at startup) — **no value reaches the
browser**:

```
NUXT_VERDIKT_API_URL=http://localhost:8000      # API the BFF proxies to
NUXT_OIDC_ISSUER=https://gitlab.example.com     # or Google / Zitadel / ...
NUXT_OIDC_CLIENT_ID=<application-id>
NUXT_OIDC_CLIENT_SECRET=<application-secret>
NUXT_SESSION_PASSWORD=<32+ char random>         # openssl rand -base64 32
```

> **GitLab**: create the OAuth application with scopes `openid email profile`,
> redirect `{origin}/auth/callback`, and **Confidential checked** (the BFF holds
> the secret). The **Application ID / Secret** are your client id / secret; the
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

After login the IdP redirects to `/auth/callback`; the **BFF** exchanges the code
for tokens server-side, stores them in the sealed session cookie, and continues
to the original destination (or `/`). Logout clears the session and redirects to
the IdP end-session endpoint.

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
   - Use: **Web** → **Code** (confidential — the BFF holds the secret).
   - Enable **Dev Mode** on the app (allows the `http://` redirect below).
   - **Redirect URI**: `http://localhost:3000/auth/callback`
   - **Post-logout redirect URI**: `http://localhost:3000/`

4. Copy the application's **Client ID** + **Secret**, then fill the env files:

   `frontend/.env`:

   ```
   NUXT_VERDIKT_API_URL=http://localhost:8000
   NUXT_OIDC_ISSUER=http://localhost:8080
   NUXT_OIDC_CLIENT_ID=<client-id>
   NUXT_OIDC_CLIENT_SECRET=<client-secret>
   NUXT_SESSION_PASSWORD=<32+ char random>
   ```

   root `.env`:

   ```
   OIDC_ISSUER=http://localhost:8080
   OIDC_AUDIENCE=<client-id>        # the id_token's aud (machines don't use OIDC)
   ```

5. Run the app and log in:

   ```shell
   make dev         # db + migrations + backend + frontend
   ```

   The frontend (Nuxt) serves at <http://localhost:3000>; an unauthenticated
   route redirects through the BFF to the Zitadel login.

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

The frontend is a Nuxt/Nitro **Node server** (`node .output/server/index.mjs`),
not static files. It reads its config from `NUXT_*` env at **server startup**
(Nuxt `runtimeConfig`), so **the same image works against any IdP** — no rebuild,
no per-customer artifact, no envsubst.

```shell
docker run -p 3000:3000 \
  -e NUXT_VERDIKT_API_URL=https://verdikt-api.your-domain \
  -e NUXT_OIDC_ISSUER=https://gitlab.example.com \
  -e NUXT_OIDC_CLIENT_ID=<client-id> \
  -e NUXT_OIDC_CLIENT_SECRET=<client-secret> \
  -e NUXT_SESSION_PASSWORD=<32+ char random> \
  ghcr.io/<owner>/evaluation-app/frontend:latest
```

| Var                       | Purpose                                            |
| ------------------------- | -------------------------------------------------- |
| `NUXT_VERDIKT_API_URL`    | Backend API the BFF proxies to (server-to-server)  |
| `NUXT_OIDC_ISSUER`        | Your IdP issuer (GitLab, Google, …)                |
| `NUXT_OIDC_CLIENT_ID`     | The confidential OAuth client id                   |
| `NUXT_OIDC_CLIENT_SECRET` | The confidential OAuth client secret               |
| `NUXT_SESSION_PASSWORD`   | Sealed-session cookie key (≥ 32 chars)             |

Because the browser only ever talks to the same-origin BFF, no OIDC/API config is
exposed client-side.

The backend reads its config from env/`.env` at startup (see
[Backend config](#3-backend-config)) — set `OIDC_ISSUER`, `OIDC_AUDIENCE`,
`ADMIN_EMAILS`, `SERVICE_BASE_URL`, and `APP_DB_*` on the container.
`SERVICE_BASE_URL` must be the backend's public URL (advertised to SDK clients as
the machine-token issuer).

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
