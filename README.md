# Verdikt

Standalone AI evaluation service that decouples evaluation and judging from the application being evaluated. Supports human and LLM-based judgment of Q&A pairs with cost tracking and judge calibration.

## Structure

- `backend/` — FastAPI REST API, LLM judge worker, PostgreSQL storage
- `frontend/` — Vue 3 SPA for human judging and viewing results

## Authentication (Zitadel)

The frontend uses Zitadel as an OIDC provider via `@zitadel/vue`. To replicate the setup:

1. Login with

```
zitadel-admin@zitadel.localhost
Password1!
```

1. Create a Zitadel project and a **User Agent** (PKCE) application.
1. Add the following **Redirect URI** in the Zitadel console:

   > Enable **Dev Mode** on the application before adding the URI.

   ```
   http://localhost:5173/auth/signinwin/zitadel
   ```

   The path is constructed as `{origin}/auth/signinwin/{authName}` where `authName` defaults to `"zitadel"`. If you run the frontend on a different port or domain, update the URI accordingly.
1. Add the following **Post-Logout Redirect URI**:

   ```
   http://localhost:5173/
   ```

1. Copy `frontend/.env.example` to `frontend/.env` and fill in:

   ```
   VITE_ZITADEL_ISSUER=https://<your-instance>.zitadel.cloud
   VITE_ZITADEL_CLIENT_ID=<your-client-id>
   VITE_ZITADEL_PROJECT_RESOURCE_ID=<your-project-resource-id>
   ```

1. After login, Zitadel redirects the browser to the redirect URI above. The app exchanges the authorization code for tokens and sends the user to their original destination (or `/`). On logout, Zitadel redirects back to `/`.

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
