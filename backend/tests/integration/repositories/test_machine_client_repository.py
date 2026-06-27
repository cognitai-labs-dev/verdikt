import pytest
from sqlalchemy.ext.asyncio import AsyncConnection

from src.repositories.machine_client import MachineClientRepository
from tests.factories.machine_client import machine_client_db_factory


@pytest.fixture
def repo() -> MachineClientRepository:
    """MachineClientRepository instance for testing."""
    return MachineClientRepository()


@pytest.mark.anyio
async def test_get_many_returns_all_inserted_clients(
    db_conn: AsyncConnection, repo: MachineClientRepository
):
    # Arrange
    client_a = await machine_client_db_factory(
        db_conn, client_id="mc-get-many-a", name="client-a"
    )
    client_b = await machine_client_db_factory(
        db_conn, client_id="mc-get-many-b", name="client-b"
    )

    # Act
    results = await repo.get_many(db_conn)

    # Assert
    returned_ids = {r.id for r in results}
    assert client_a.id in returned_ids
    assert client_b.id in returned_ids


@pytest.mark.anyio
async def test_set_revoked_true_marks_client_as_revoked(
    db_conn: AsyncConnection, repo: MachineClientRepository
):
    # Arrange
    client = await machine_client_db_factory(
        db_conn, client_id="mc-revoke-true", revoked=False
    )

    # Act
    result = await repo.set_revoked(db_conn, client.client_id, True)

    # Assert
    assert result is not None
    assert result.revoked is True
    assert result.client_id == "mc-revoke-true"


@pytest.mark.anyio
async def test_set_revoked_false_unrevokes_client(
    db_conn: AsyncConnection, repo: MachineClientRepository
):
    # Arrange
    client = await machine_client_db_factory(
        db_conn, client_id="mc-revoke-false", revoked=True
    )

    # Act
    result = await repo.set_revoked(db_conn, client.client_id, False)

    # Assert
    assert result is not None
    assert result.revoked is False
    assert result.client_id == "mc-revoke-false"
