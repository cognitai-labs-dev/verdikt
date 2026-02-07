import pytest
from sqlalchemy.ext.asyncio import AsyncConnection

from src.constants import EvaluationType
from src.repositories.evaluation import EvaluationsRepository
from src.schemas.base import UpdateSchema
from tests.factories.evaluation import (
    evaluation_create_schema_factory,
    evaluation_db_schema_factory,
)


@pytest.fixture
def repo() -> EvaluationsRepository:
    """EvaluationsRepository instance for testing base methods."""
    return EvaluationsRepository()


@pytest.mark.anyio
async def test_create_returns_schema_with_generated_id(
    db_conn: AsyncConnection, repo: EvaluationsRepository
):
    # Arrange
    create_schema = evaluation_create_schema_factory(app_id="my-app")

    # Act
    result = await repo.create(db_conn, create_schema)

    # Assert
    assert result.id is not None
    assert result.app_id == "my-app"
    assert result.app_version == "1.0.0"
    assert result.type == EvaluationType.LLM_ONLY


@pytest.mark.anyio
async def test_create_many_returns_all_created_records(
    db_conn: AsyncConnection, repo: EvaluationsRepository
):
    # Arrange
    schemas = [
        evaluation_create_schema_factory(app_id="app-1"),
        evaluation_create_schema_factory(app_id="app-2"),
        evaluation_create_schema_factory(app_id="app-3"),
    ]

    # Act
    results = await repo.create_many(db_conn, schemas)

    # Assert
    assert len(results) == 3
    assert results[0].app_id == "app-1"
    assert results[1].app_id == "app-2"
    assert results[2].app_id == "app-3"


@pytest.mark.anyio
async def test_create_many_returns_empty_list_when_given_empty_list(
    db_conn: AsyncConnection, repo: EvaluationsRepository
):
    # Act
    results = await repo.create_many(db_conn, [])

    # Assert
    assert results == []


@pytest.mark.anyio
async def test_get_returns_record_by_id(
    db_conn: AsyncConnection, repo: EvaluationsRepository
):
    # Arrange
    created = await evaluation_db_schema_factory(
        db_conn=db_conn, app_id="fetch-me"
    )

    # Act
    result = await repo.get(db_conn, created.id)

    # Assert
    assert result is not None
    assert result.id == created.id
    assert result.app_id == "fetch-me"


@pytest.mark.anyio
async def test_get_returns_none_when_id_does_not_exist(
    db_conn: AsyncConnection, repo: EvaluationsRepository
):
    # Act
    result = await repo.get(db_conn, 999999)

    # Assert
    assert result is None


@pytest.mark.anyio
async def test_get_by_many_ids_returns_matching_records(
    db_conn: AsyncConnection, repo: EvaluationsRepository
):
    # Arrange
    eval_1 = await evaluation_db_schema_factory(
        db_conn=db_conn, app_id="a"
    )
    eval_2 = await evaluation_db_schema_factory(
        db_conn=db_conn, app_id="b"
    )
    await evaluation_db_schema_factory(db_conn=db_conn, app_id="c")

    # Act
    results = await repo.get_by_many_ids(
        db_conn, [eval_1.id, eval_2.id]
    )

    # Assert
    assert len(results) == 2
    returned_ids = {r.id for r in results}
    assert returned_ids == {eval_1.id, eval_2.id}


@pytest.mark.anyio
async def test_get_by_many_ids_returns_empty_list_when_given_empty_list(
    db_conn: AsyncConnection, repo: EvaluationsRepository
):
    # Act
    results = await repo.get_by_many_ids(db_conn, [])

    # Assert
    assert results == []


@pytest.mark.anyio
async def test_update_returns_updated_record(
    db_conn: AsyncConnection, repo: EvaluationsRepository
):
    # Arrange
    created = await evaluation_db_schema_factory(
        db_conn=db_conn, app_version="1.0.0"
    )
    update_data = UpdateSchema(id=created.id)

    # Act
    result = await repo.update(db_conn, update_data)

    # Assert
    assert result is not None
    assert result.id == created.id
    assert result.app_version == "1.0.0"


@pytest.mark.anyio
async def test_update_returns_unchanged_record_when_no_fields_provided(
    db_conn: AsyncConnection, repo: EvaluationsRepository
):
    # Arrange
    created = await evaluation_db_schema_factory(
        db_conn=db_conn, app_id="unchanged"
    )
    update_data = UpdateSchema(id=created.id)

    # Act
    result = await repo.update(db_conn, update_data)

    # Assert
    assert result is not None
    assert result.app_id == "unchanged"


@pytest.mark.anyio
async def test_update_returns_none_when_id_does_not_exist(
    db_conn: AsyncConnection, repo: EvaluationsRepository
):
    # Act
    result = await repo.update(db_conn, UpdateSchema(id=999999))

    # Assert
    assert result is None
