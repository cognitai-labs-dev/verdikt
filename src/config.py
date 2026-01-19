from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    APP_ENV: str = "dev"
    LOG_LEVEL: str = "INFO"

    OPENAI_API_KEY: str

    LLM_MODEL: str = "gpt-4o-mini"

    PG_HOST: str = "localhost"
    PG_PORT: str = "5433"
    PG_USER: str = "postgresql"
    PG_PASSWORD: str = "alpharius"

    @property
    def postgresql(self):
        return f"postgresql+psycopg://{self.PG_USER}:{self.PG_PASSWORD}@{self.PG_HOST}:{self.PG_PORT}"




settings = Settings()
