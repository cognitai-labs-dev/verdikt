from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict
from yalc import LLMModel

ROOT_DIR = Path(__file__).parent.parent

settings_config_dict = SettingsConfigDict(
    env_file=".env", extra="ignore"
)


class AppSettings(BaseSettings):
    model_config = settings_config_dict

    APP_ENV: str = "dev"
    LOG_LEVEL: str = "INFO"


class PostgresSettings(BaseSettings):
    model_config = settings_config_dict

    PG_HOST: str = "localhost"
    PG_PORT: str = "5433"
    PG_USER: str = "postgresql"
    PG_PASSWORD: str = "alpharius"
    PG_DB: str = "evaluation"

    @property
    def postgres_dsn(self):
        return f"postgresql+psycopg://{self.PG_USER}:{self.PG_PASSWORD}@{self.PG_HOST}:{self.PG_PORT}/{self.PG_DB}"


class LLMSettings(BaseSettings):
    model_config = settings_config_dict

    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""

    JUDGING_LLM_MODELS: list[LLMModel] = [
        LLMModel.gpt_4o_mini,
        LLMModel.gpt_5_mini,
        LLMModel.claude_sonnet_4_5,
    ]

    WORKER_WAIT_TIME: int = 5
    WORKER_BATCH_SIZE: int = 10


class ProcessorSettings(LLMSettings, PostgresSettings):
    pass


class APISettings(PostgresSettings):
    pass
