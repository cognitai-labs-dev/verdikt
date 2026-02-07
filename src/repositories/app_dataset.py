from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncConnection

from src.db.tables.app_datasets import app_datasets_table
from src.repositories.base import BaseRepository
from src.schemas.app_dataset import (
    AppDatasetCreateSchema,
    AppDatasetSchema,
    AppDatasetUpdateSchema,
)


class AppDatasetRepository(
    BaseRepository[
        AppDatasetCreateSchema,
        AppDatasetSchema,
        AppDatasetUpdateSchema,
    ]
):
    """Data access layer for app dataset operations."""

    def __init__(self):
        super().__init__(app_datasets_table, AppDatasetSchema)

    async def get_many_by_app_id(
        self, conn: AsyncConnection, app_id: int
    ) -> list[AppDatasetSchema]:
        """Get all dataset entries for a given app ID."""
        stmt = (
            select(app_datasets_table)
            .where(app_datasets_table.c.app_id == app_id)
            .order_by(app_datasets_table.c.created_at.desc())
        )

        result = await conn.execute(stmt)
        rows = result.fetchall()

        if len(rows) == 0:
            return []
        return [
            AppDatasetSchema.model_validate(row._mapping)
            for row in rows
        ]
