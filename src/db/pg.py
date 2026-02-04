import logging

from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

sa_metadata = MetaData(
    naming_convention={
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_N_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_N_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    }
)


class DBAdapter:
    def __init__(self) -> None:
        self._engine: AsyncEngine | None = None
        self.logger = logging.getLogger(__name__)

    @property
    def engine(self) -> AsyncEngine:
        if self._engine is None:
            raise RuntimeError("Engine not initlized")
        return self._engine

    async def connect(self, dsn: str) -> AsyncEngine:
        if self._engine:
            self.logger.info("DB engine already exists")
            return self._engine

        self._engine = create_async_engine(dsn)
        self.logger.info(
            "Connected to Postgresql server: %s", self._engine.url
        )
        return self._engine

    async def disconnect(self) -> None:
        if self._engine:
            await self._engine.dispose()
            self.logger.info("Disconnected from Postgresql server")


db = DBAdapter()
