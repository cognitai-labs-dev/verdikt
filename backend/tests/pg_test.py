from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncEngine,
    create_async_engine,
)


class AsyncEngineTestWrapper:
    def __init__(self, dsn: str, **kwargs):
        self.engine: AsyncEngine = create_async_engine(dsn, **kwargs)

        self.conn: AsyncConnection | None = None

    async def __aenter__(self):
        await self.drop_db_tables()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.drop_db_tables()
        await self.engine.dispose()

    def __getattr__(self, name):
        return getattr(self.db_engine, name)

    @asynccontextmanager
    async def real_begin(
        self,
    ) -> AsyncGenerator[AsyncConnection, Any]:
        """
        Called at the beginning of each testcase, by the `db_conn` fixture.
        It will create a testcase-wide connection that will rollback at the end
        of testcase.
        """
        async with self.engine.begin() as conn:
            self.conn = conn
            yield self.conn
            await conn.rollback()

    @asynccontextmanager
    async def begin(self) -> AsyncGenerator[AsyncConnection, Any]:
        """
        Override the default `AsyncEngine.begin()`. Instead of creating
        a new connection it will return the common testcase-wide connection.
        """
        if not self.conn:
            raise RuntimeError(
                "No db connection established (did you forget to pass `db_conn` argument to the test?)"
            )

        yield self.conn

    @asynccontextmanager
    async def connect(self) -> AsyncGenerator[AsyncConnection, Any]:
        """
        Override the default `AsyncEngine.connect()`. Instead of creating
        a new connection it will return the common testcase-wide connection.
        """
        async with self.begin() as db_conn:
            yield db_conn

    async def drop_db_tables(self):
        async with self.engine.begin() as conn:
            select_all_tables_stmt = (
                sa.select(sa.column("tablename").label("name"))
                .select_from(sa.text("pg_tables"))
                .where(sa.literal_column("schemaname") == "public")
            )
            for table in await conn.execute(select_all_tables_stmt):
                stmt = sa.text(
                    f"DROP TABLE IF EXISTS {table.name} CASCADE"
                )
                await conn.execute(stmt)
