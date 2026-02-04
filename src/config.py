from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

from llm import LLMModel

ROOT_DIR = Path(__file__).parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    APP_ENV: str = "dev"
    LOG_LEVEL: str = "INFO"

    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""

    JUDGING_LLM_MODELS: list[LLMModel] = [
        LLMModel.gpt_4o_mini,
        LLMModel.gpt_5_mini,
        LLMModel.claude_sonnet_4_5,
    ]

    PG_HOST: str = "localhost"
    PG_PORT: str = "5433"
    PG_USER: str = "postgresql"
    PG_PASSWORD: str = "alpharius"

    WORKER_WAIT_TIME: int = 5
    WORKER_BATCH_SIZE: int = 10

    @property
    def postgresql(self):
        return f"postgresql+psycopg://{self.PG_USER}:{self.PG_PASSWORD}@{self.PG_HOST}:{self.PG_PORT}"

    @property
    def is_dev(self) -> bool:
        return self.APP_ENV.lower() == "dev"


settings = Settings()
