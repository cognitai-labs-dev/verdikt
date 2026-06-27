from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict
from yalc import LLMModel

# Single repo-root .env, shared with docker-compose. Resolved absolutely so it
# loads regardless of the process working directory (backend/, tests, etc.).
_ROOT_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"

settings_config_dict = SettingsConfigDict(
    env_file=_ROOT_ENV_FILE, extra="ignore"
)


class AppSettings(BaseSettings):
    model_config = settings_config_dict

    APP_ENV: str = "dev"
    LOG_LEVEL: str = "INFO"


class PostgresSettings(BaseSettings):
    model_config = settings_config_dict

    # Same APP_DB_* names the docker-compose init script uses (docker/init-db.sh)
    # so DB credentials live once in the root .env. HOST/PORT are the connection
    # target from the backend process (localhost; compose maps 5432 -> 5433).
    APP_DB_HOST: str = "localhost"
    APP_DB_PORT: str = "5433"
    APP_DB_USER: str = "evaluation"
    APP_DB_PASSWORD: str = "alpharius"
    APP_DB_NAME: str = "evaluation"

    @property
    def postgres_dsn(self):
        return f"postgresql+psycopg://{self.APP_DB_USER}:{self.APP_DB_PASSWORD}@{self.APP_DB_HOST}:{self.APP_DB_PORT}/{self.APP_DB_NAME}"


class LLMSettings(BaseSettings):
    model_config = settings_config_dict

    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""

    JUDGING_LLM_MODELS: list[LLMModel] = [
        LLMModel.gpt_4o_mini,
        LLMModel.gpt_5_mini,
    ]

    WORKER_WAIT_TIME: int = 5
    WORKER_BATCH_SIZE: int = 10


class ProcessorSettings(LLMSettings, PostgresSettings):
    pass


class APISettings(PostgresSettings):
    # Generic OIDC config — point at any OIDC-compliant provider
    # (Google, Zitadel, Keycloak, Okta, Azure AD, ...).
    OIDC_ISSUER: str = "http://localhost:8080"
    # Comma-separated list of accepted audiences. Different clients put
    # different values in `aud` (e.g. the frontend SPA client id vs. the SDK
    # machine client id), so list every client that calls this API.
    OIDC_AUDIENCE: str = ""
    # Optional explicit JWKS URI. If empty, discovered from the issuer's
    # {OIDC_ISSUER}/.well-known/openid-configuration document.
    OIDC_JWKS_URI: str = ""
    JWT_ALGORITHMS: list[str] = ["RS256"]

    # Comma-separated emails granted admin (access to every app). Humans whose
    # OIDC `email` claim is listed here resolve to an admin Principal.
    ADMIN_EMAILS: str = ""

    # Verdikt's own public URL, advertised as the machine (M2M) issuer. Machine
    # auth never touches the human login IdP — Verdikt mints its own opaque
    # client_credentials tokens, so `make eval` works under any login provider.
    SERVICE_BASE_URL: str = "http://localhost:8000"
    MACHINE_TOKEN_TTL: int = 3600

    @property
    def oidc_audiences(self) -> list[str]:
        return [
            a.strip()
            for a in self.OIDC_AUDIENCE.split(",")
            if a.strip()
        ]

    @property
    def admin_emails(self) -> list[str]:
        return [
            e.strip()
            for e in self.ADMIN_EMAILS.split(",")
            if e.strip()
        ]
