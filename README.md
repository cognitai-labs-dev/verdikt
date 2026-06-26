# Verdikt

Standalone AI evaluation service that decouples evaluation and judging from the application being evaluated. Supports human and LLM-based judgment of Q&A pairs with cost tracking and judge calibration.

## Structure

- `backend/` — FastAPI REST API, LLM judge worker, PostgreSQL storage
- `frontend/` — Vue 3 SPA for human judging and viewing results

## Authentication (generic OIDC)

Verdikt authenticates against any **OIDC-compliant** provider — Google
Workspace, Zitadel, Keycloak, Authentik, Okta, Azure AD, etc. Pick one per
deployment and configure it via environment variables. The frontend runs the
authorization-code + PKCE flow and sends the **id_token** to the backend, which
verifies it against the issuer's JWKS.

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
# Zitadel
VITE_OIDC_ISSUER=https://<your-instance>.zitadel.cloud
VITE_OIDC_CLIENT_ID=<your-client-id>

# Google
VITE_OIDC_ISSUER=https://accounts.google.com
VITE_OIDC_CLIENT_ID=<your-client-id>
```

### 3. Backend config

Copy `.env.example` to `.env`:

```
OIDC_ISSUER=http://localhost:8080   # must match the token's `iss`
OIDC_AUDIENCE=<your-client-id>      # the token's `aud`
```

The JWKS URI is auto-discovered from the issuer's
`/.well-known/openid-configuration`. Set `OIDC_JWKS_URI` only to pin it
explicitly.

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
   OIDC_AUDIENCE=<client-id>        # comma-separated; add the SDK id too (below)
   ```

5. Run the app and log in:

   ```shell
   make dev         # db + migrations + backend + frontend
   ```

   The frontend is served at <http://localhost:5173>; an unauthenticated route
   redirects to the Zitadel login.

### SDK access (machine user)

The Python SDK authenticates with the OAuth2 **client-credentials** grant,
which in Zitadel means a **Service User**. Service Users are **org-level** —
they survive project deletion, unlike the SPA app above.

1. Console → **Users** → **Service Users** → **+ New**.
   - **Username**: e.g. `sdk-test` (this becomes the client id **and** the
     token's `aud`).
   - **Access Token Type**: `Bearer`. Create.

2. Open the service user → **Client Secret** → **Generate**. Copy the
   **Client ID** (the username) and the **Client Secret** — the secret is shown
   once.

3. Add them to root `.env`, and append the SDK's id to the audience allowlist
   so the backend accepts its token:

   ```
   VERDIKT_CLIENT_ID=sdk-test
   VERDIKT_CLIENT_SECRET=<generated-secret>
   OIDC_AUDIENCE=<spa-client-id>,sdk-test
   ```

   Restart the backend after changing `.env` (it reads it at startup).

> The SDK token's `aud` is the service user's id, which differs from the SPA
> client id — that's why `OIDC_AUDIENCE` is a list. See the SDK repo for client
> usage.

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
`OIDC_ISSUER`, `OIDC_AUDIENCE`, and `APP_DB_*` on the container.

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
