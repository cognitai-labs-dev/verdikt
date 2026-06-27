from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncConnection

from src.constants import SubjectType
from src.db.tables.app_principals import app_principals_table
from src.repositories.base import BaseRepository
from src.schemas.app_principal import (
    AppPrincipalCreateSchema,
    AppPrincipalSchema,
    AppPrincipalUpdateSchema,
)


class AppPrincipalRepository(
    BaseRepository[
        AppPrincipalCreateSchema,
        AppPrincipalSchema,
        AppPrincipalUpdateSchema,
    ]
):
    """Data access layer for per-app principal bindings."""

    def __init__(self):
        super().__init__(app_principals_table, AppPrincipalSchema)

    async def app_ids_for(
        self,
        conn: AsyncConnection,
        subject_type: SubjectType,
        subject: str,
    ) -> list[int]:
        """App ids a (subject_type, subject) is bound to."""
        stmt = select(self.table.c.app_id).where(
            self.table.c.subject_type == subject_type,
            self.table.c.subject == subject,
        )
        result = await conn.execute(stmt)
        return [row.app_id for row in result.fetchall()]

    async def add(
        self,
        conn: AsyncConnection,
        app_id: int,
        subject_type: SubjectType,
        subject: str,
    ) -> AppPrincipalSchema:
        return await self.create(
            conn,
            AppPrincipalCreateSchema(
                app_id=app_id,
                subject_type=subject_type,
                subject=subject,
            ),
        )

    async def remove(
        self,
        conn: AsyncConnection,
        app_id: int,
        subject_type: SubjectType,
        subject: str,
    ) -> None:
        """Delete the binding matching (app_id, subject_type, subject)."""
        stmt = delete(self.table).where(
            self.table.c.app_id == app_id,
            self.table.c.subject_type == subject_type,
            self.table.c.subject == subject,
        )
        await conn.execute(stmt)
