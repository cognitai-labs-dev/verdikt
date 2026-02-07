import logging
from pathlib import Path
from typing import Any, AsyncGenerator

import pytest
from alembic.config import Config as AlembicConfig
from sqlalchemy.ext.asyncio import AsyncConnection

from alembic import command as alembic_command
from src.config import PostgresSettings
from tests.pg_test import AsyncEngineTestWrapper


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session")
async def db_engine() -> AsyncGenerator[AsyncEngineTestWrapper, Any]:
    settings = PostgresSettings()
    async with AsyncEngineTestWrapper(
        settings.postgres_dsn
    ) as engine:
        logging.getLogger("alembic").setLevel(logging.CRITICAL)
        logging.getLogger("one_offer_rank.db.mongo").setLevel(
            logging.CRITICAL
        )
        alembic_config_path = (
            Path(__name__).absolute().parent / "alembic.ini"
        )
        alembic_command.upgrade(
            AlembicConfig(str(alembic_config_path)), "head"
        )

        yield engine


@pytest.fixture
async def db_conn(
    db_engine: AsyncEngineTestWrapper,
) -> AsyncGenerator[AsyncConnection, Any]:
    async with db_engine.real_begin() as conn:
        yield conn
