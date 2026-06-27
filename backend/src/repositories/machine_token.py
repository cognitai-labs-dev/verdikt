from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncConnection

from src.db.tables.machine_tokens import machine_tokens_table
from src.repositories.base import BaseRepository
from src.schemas.machine_token import (
    MachineTokenCreateSchema,
    MachineTokenSchema,
    MachineTokenUpdateSchema,
)


class MachineTokenRepository(
    BaseRepository[
        MachineTokenCreateSchema,
        MachineTokenSchema,
        MachineTokenUpdateSchema,
    ]
):
    """Data access layer for machine token operations."""

    def __init__(self):
        super().__init__(machine_tokens_table, MachineTokenSchema)

    async def get_by_hash(
        self, conn: AsyncConnection, token_hash: str
    ) -> MachineTokenSchema | None:
        stmt = select(self.table).where(
            self.table.c.token_hash == token_hash
        )
        result = await conn.execute(stmt)
        row = result.fetchone()
        if row is None:
            return None
        return self.schema.model_validate(row._mapping)

    async def revoke_for_client(
        self, conn: AsyncConnection, client_id: str
    ) -> int:
        """Revoke every live token of a client. Returns rows affected."""
        stmt = (
            update(self.table)
            .where(self.table.c.client_id == client_id)
            .values(revoked=True)
        )
        result = await conn.execute(stmt)
        return result.rowcount
