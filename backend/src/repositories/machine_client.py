from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncConnection

from src.db.tables.machine_clients import machine_clients_table
from src.repositories.base import BaseRepository
from src.schemas.machine_client import (
    MachineClientCreateSchema,
    MachineClientSchema,
    MachineClientUpdateSchema,
)


class MachineClientRepository(
    BaseRepository[
        MachineClientCreateSchema,
        MachineClientSchema,
        MachineClientUpdateSchema,
    ]
):
    """Data access layer for machine client operations."""

    def __init__(self):
        super().__init__(machine_clients_table, MachineClientSchema)

    async def get_by_client_id(
        self, conn: AsyncConnection, client_id: str
    ) -> MachineClientSchema | None:
        stmt = select(self.table).where(
            self.table.c.client_id == client_id
        )
        result = await conn.execute(stmt)
        row = result.fetchone()
        if row is None:
            return None
        return self.schema.model_validate(row._mapping)
