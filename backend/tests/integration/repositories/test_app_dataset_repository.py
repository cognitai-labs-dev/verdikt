import pytest
from sqlalchemy.ext.asyncio import AsyncConnection

from src.repositories.app_dataset import AppDatasetRepository
from tests.factories.app import app_db_schema_factory
from tests.factories.app_dataset import app_dataset_db_schema_factory


@pytest.fixture
def repo() -> AppDatasetRepository:
    """AppDatasetRepository instance for testing."""
    return AppDatasetRepository()


@pytest.mark.anyio
async def test_get_many_by_app_id_returns_datasets_for_given_app(
    db_conn: AsyncConnection, repo: AppDatasetRepository
):
    # Arrange
    app = await app_db_schema_factory(db_conn)
    other_app = await app_db_schema_factory(db_conn, name="other-app")

    # matching app_id
    await app_dataset_db_schema_factory(
        db_conn, app_id=app.id, question="Q1"
    )
    await app_dataset_db_schema_factory(
        db_conn, app_id=app.id, question="Q2"
    )
    # different app_id — must not appear
    await app_dataset_db_schema_factory(
        db_conn, app_id=other_app.id, question="Q3"
    )

    # Act
    results = await repo.get_many_by_app_id(db_conn, app.id)

    # Assert
    assert len(results) == 2
    questions = {r.question for r in results}
    assert questions == {"Q1", "Q2"}


@pytest.mark.anyio
async def test_delete_removes_dataset_by_id(
    db_conn: AsyncConnection, repo: AppDatasetRepository
):
    # Arrange
    app = await app_db_schema_factory(db_conn)
    dataset = await app_dataset_db_schema_factory(db_conn, app_id=app.id)

    # Act
    deleted = await repo.delete(db_conn, dataset.id)

    # Assert
    assert deleted is True
    remaining = await repo.get_many_by_app_id(db_conn, app.id)
    assert len(remaining) == 0


@pytest.mark.anyio
async def test_delete_returns_false_when_id_missing(
    db_conn: AsyncConnection, repo: AppDatasetRepository
):
    # Act
    deleted = await repo.delete(db_conn, 999999)

    # Assert
    assert deleted is False
