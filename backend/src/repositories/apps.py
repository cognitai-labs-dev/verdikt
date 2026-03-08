from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncConnection

from src.db.tables.apps import apps_table
from src.repositories.base import BaseRepository
from src.schemas.app import (
    AppCreateSchema,
    AppSchema,
    AppUpdateSchema,
)


class AppsRepository(
    BaseRepository[AppCreateSchema, AppSchema, AppUpdateSchema]
):
    """Data access layer for apps operations."""

    def __init__(self):
        super().__init__(apps_table, AppSchema)

    async def get_many(self, conn: AsyncConnection):
        stmt = select(self.table).order_by(
            self.table.c.created_at.desc()
        )

        result = await conn.execute(stmt)
        rows = result.fetchall()

        if len(rows) == 0:
            return []

        return [
            self.schema.model_validate(row._mapping) for row in rows
        ]

    async def get_by_slug(
        self, conn: AsyncConnection, slug: str
    ) -> AppSchema | None:
        """Get an app by its unique slug."""
        stmt = select(self.table).where(self.table.c.slug == slug)
        result = await conn.execute(stmt)
        row = result.fetchone()
        if row is None:
            return None
        return self.schema.model_validate(row._mapping)
