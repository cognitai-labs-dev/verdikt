import itertools

from sqlalchemy.ext.asyncio import AsyncConnection

from src.auth.hashing import sha256_hex
from src.repositories.machine_client import MachineClientRepository
from src.schemas.machine_client import (
    MachineClientCreateSchema,
    MachineClientSchema,
    MachineClientUpdateSchema,
)

_counter = itertools.count(1)


async def machine_client_db_factory(
    db_conn: AsyncConnection,
    client_id: str | None = None,
    secret: str = "plain-secret",
    name: str = "test-client",
    is_admin: bool = False,
    revoked: bool = False,
) -> MachineClientSchema:
    """Create a machine client. `secret` is the plaintext the caller knows."""
    repo = MachineClientRepository()
    client = await repo.create(
        db_conn,
        MachineClientCreateSchema(
            client_id=client_id or f"mc-{next(_counter)}",
            client_secret_hash=sha256_hex(secret),
            name=name,
            is_admin=is_admin,
        ),
    )
    if revoked:
        updated = await repo.update(
            db_conn,
            MachineClientUpdateSchema(id=client.id, revoked=True),
        )
        assert updated is not None
        return updated
    return client
