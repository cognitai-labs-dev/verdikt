# verdikt Helm chart

Generic chart for deploying [Verdikt](https://github.com/cognitai-labs-dev/verdikt)
— API, frontend (Nuxt BFF), continuous judging worker, and an alembic
migration hook. Published to `oci://ghcr.io/cognitai-labs-dev/verdikt/charts`
on every master merge.

Intended to be consumed from your own deploy repo (as an OCI dependency of an
umbrella chart, or directly with `helm upgrade --install ... -f your-values.yaml`).

## What it deploys

| Component | Kind | Notes |
|---|---|---|
| `<name>-api` | Deployment + Service | FastAPI backend, port 8000 |
| `<name>-frontend` | Deployment + Service | Nuxt BFF, port 3000; proxies to the API in-cluster |
| `<name>-judging` | Deployment | continuous worker polling pending LLM judgments (`judging.enabled`) |
| `<name>-migrate-db` | Job (helm hook) | `alembic upgrade head` on install/upgrade, before pods roll |
| `<name>-access` | ConfigMap | rendered from `access:` values; API pods restart on change (checksum) |

No Ingress is created — bring your own and route one host to
`<name>-frontend` and one to `<name>-api` (both ClusterIP, port 80).

## Required values

```yaml
image:
  repository: ghcr.io/cognitai-labs-dev/verdikt/backend
  tag: sha-abc1234
frontendImage:
  repository: ghcr.io/cognitai-labs-dev/verdikt/frontend
  tag: sha-abc1234

api:
  # MUST equal the external API URL (the `api` ingress host) — the machine
  # token issuer and SDK discovery derive from it.
  serviceBaseUrl: https://api.verdikt.example.com
  oidc:
    issuer: https://accounts.google.com   # human-login OIDC provider
    audience: "<oauth-client-id>"

frontend:
  oidc:
    issuer: https://accounts.google.com

postgres:
  host: <db-host>
  user: verdikt
  dbName: verdikt

access:            # admins + per-app email access, reconciled on startup
  admins:
    - you@example.com
  apps: {}
```

## Secrets (bring your own)

The chart does not create secrets — provision them yourself (plain Secrets,
ExternalSecrets, sealed-secrets, ...):

| Secret | Keys |
|---|---|
| `<name>-backend` | `APP_DB_PASSWORD`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY` |
| `<name>-frontend` | `NUXT_OIDC_CLIENT_ID`, `NUXT_OIDC_CLIENT_SECRET`, `NUXT_SESSION_PASSWORD` (≥32 chars) |

`<name>` is `deployment.name` (default `verdikt`).

The database itself is also not managed here — point `postgres.*` at your own
PostgreSQL and put the password in the backend secret.

## Notes

- OIDC redirect URI to register in your IdP: `{frontend-origin}/auth/callback`
- The API host must be reachable by SDK/machine clients (it is its own
  OAuth2 client-credentials issuer at `{serviceBaseUrl}/auth/token`)
- See `values.yaml` for every knob (replicas, resources, security contexts,
  judging worker tuning, CORS, token TTL, ...)
