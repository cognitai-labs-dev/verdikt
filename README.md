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

## Quick Start

```shell
make api      # start DB + migrations + API server
make eval # seed with mock data
make judge    # run LLM judgment worker
make fe       # start frontend dev server
```

## Testing

```shell
make test     # backend tests
make lint     # pre-commit hooks (backend + frontend)
```
