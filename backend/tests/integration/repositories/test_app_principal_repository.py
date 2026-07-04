import pytest
from sqlalchemy.ext.asyncio import AsyncConnection

from src.constants import SubjectType
from src.repositories.app_principal import AppPrincipalRepository
from tests.factories.app import app_db_schema_factory


@pytest.fixture
def repo() -> AppPrincipalRepository:
    """AppPrincipalRepository instance for testing."""
    return AppPrincipalRepository()


@pytest.mark.anyio
async def test_remove_deletes_matching_binding(
    db_conn: AsyncConnection, repo: AppPrincipalRepository
):
    # Arrange
    app = await app_db_schema_factory(db_conn)
    await repo.add(db_conn, app.id, SubjectType.CLIENT, "mc-to-remove")

    # Act
    await repo.remove(
        db_conn, app.id, SubjectType.CLIENT, "mc-to-remove"
    )

    # Assert
    remaining = await repo.app_ids_for(
        db_conn, SubjectType.CLIENT, "mc-to-remove"
    )
    assert app.id not in remaining


@pytest.mark.anyio
async def test_remove_leaves_other_bindings_intact(
    db_conn: AsyncConnection, repo: AppPrincipalRepository
):
    # Arrange
    app_a = await app_db_schema_factory(db_conn)
    app_b = await app_db_schema_factory(db_conn)
    # binding to remove
    await repo.add(db_conn, app_a.id, SubjectType.CLIENT, "mc-remove-a")
    # binding that must survive
    await repo.add(db_conn, app_b.id, SubjectType.CLIENT, "mc-remove-a")

    # Act
    await repo.remove(
        db_conn, app_a.id, SubjectType.CLIENT, "mc-remove-a"
    )

    # Assert
    remaining = await repo.app_ids_for(
        db_conn, SubjectType.CLIENT, "mc-remove-a"
    )
    assert app_a.id not in remaining
    assert app_b.id in remaining
