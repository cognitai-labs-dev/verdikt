from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncConnection

from src.db.tables.apps import apps_table
from src.repositories.base import BaseRepository
from src.schemas.app import AppCreateSchema, AppSchema
from src.schemas.base import UpdateSchema


class AppsRepository(
    BaseRepository[AppCreateSchema, AppSchema, UpdateSchema]
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
