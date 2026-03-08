import pytest
from sqlalchemy.ext.asyncio import AsyncConnection

from src.app.queries import AppDatasetQueries
from src.repositories.app_dataset import AppDatasetRepository
from tests.factories.app import app_db_schema_factory
from tests.factories.app_dataset import app_dataset_db_schema_factory


@pytest.fixture
def repo() -> AppDatasetRepository:
    """AppDatasetRepository instance for testing."""
    return AppDatasetRepository()


@pytest.fixture
def queries(repo: AppDatasetRepository) -> AppDatasetQueries:
    """AppDatasetQueries instance for testing."""
    return AppDatasetQueries(app_dataset_repo=repo)


@pytest.mark.anyio
async def test_sync_datasets_handles_mix_of_insert_update_and_noop(
    db_conn: AsyncConnection,
    queries: AppDatasetQueries,
    repo: AppDatasetRepository,
):
    # Arrange
    app = await app_db_schema_factory(db_conn)
    # noop — identical
    await app_dataset_db_schema_factory(
        db_conn,
        app_id=app.id,
        question="Unchanged Q",
        human_answer="Same answer",
    )
    # will be updated — answer differs
    updated_existing = await app_dataset_db_schema_factory(
        db_conn,
        app_id=app.id,
        question="Update Q",
        human_answer="Old answer",
    )

    # Act — also includes a brand new question
    _, any_inserted = await queries.sync_datasets(
        db_conn,
        app.id,
        [
            ("Unchanged Q", "Same answer"),
            ("Update Q", "New answer"),
            ("Brand new Q", "Fresh answer"),
        ],
    )

    # Assert
    assert any_inserted is True
    rows = await repo.get_many_by_app_id(db_conn, app.id)
    assert len(rows) == 3
    by_question = {r.question: r for r in rows}
    assert by_question["Unchanged Q"].human_answer == "Same answer"
    assert by_question["Brand new Q"].human_answer == "Fresh answer"
    updated_row = await repo.get(db_conn, updated_existing.id)
    assert updated_row is not None
    assert updated_row.human_answer == "New answer"
