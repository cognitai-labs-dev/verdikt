from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncConnection

from src.db.tables.prompt_versions import (
    prompt_versions_table,
)
from src.repositories.base import BaseRepository
from src.schemas.base import UpdateSchema
from src.schemas.prompt_version import (
    PromptVersionCreateSchema,
    PromptVersionSchema,
)


class PromptVersionRepository(
    BaseRepository[
        PromptVersionCreateSchema,
        PromptVersionSchema,
        UpdateSchema,
    ]
):
    """Data access layer for prompt versions."""

    def __init__(self):
        super().__init__(prompt_versions_table, PromptVersionSchema)

    async def get_many_by_app_id(
        self, conn: AsyncConnection, app_id: int
    ) -> list[PromptVersionSchema]:
        stmt = (
            select(self.table)
            .where(self.table.c.app_id == app_id)
            .order_by(self.table.c.created_at.desc())
        )

        result = await conn.execute(stmt)
        rows = result.fetchall()

        if len(rows) == 0:
            return []
        return [
            self.schema.model_validate(row._mapping) for row in rows
        ]
