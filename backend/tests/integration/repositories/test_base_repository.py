import pytest
from sqlalchemy.ext.asyncio import AsyncConnection

from src.repositories.apps import AppsRepository
from src.schemas.base import UpdateSchema
from tests.factories.app import (
    app_create_schema_factory,
    app_db_schema_factory,
)


@pytest.fixture
def repo() -> AppsRepository:
    """AppsRepository instance for testing base methods."""
    return AppsRepository()


@pytest.mark.anyio
async def test_create_returns_schema_with_generated_id(
    db_conn: AsyncConnection, repo: AppsRepository
):
    # Arrange
    create_schema = app_create_schema_factory(name="app-1")

    # Act
    result = await repo.create(db_conn, create_schema)

    # Assert
    assert result.id is not None
    assert result.name == "app-1"


@pytest.mark.anyio
async def test_create_many_returns_all_created_records(
    db_conn: AsyncConnection, repo: AppsRepository
):
    # Arrange
    schemas = [
        app_create_schema_factory(name="app-1"),
        app_create_schema_factory(name="app-2"),
    ]

    # Act
    results = await repo.create_many(db_conn, schemas)

    # Assert
    assert len(results) == 2
    assert results[0].name == "app-1"
    assert results[1].name == "app-2"


@pytest.mark.anyio
async def test_create_many_returns_empty_list_when_given_empty_list(
    db_conn: AsyncConnection, repo: AppsRepository
):
    # Act
    results = await repo.create_many(db_conn, [])

    # Assert
    assert results == []


@pytest.mark.anyio
async def test_get_returns_record_by_id(
    db_conn: AsyncConnection, repo: AppsRepository
):
    # Arrange
    created = await app_db_schema_factory(
        db_conn=db_conn, name="fetch-me"
    )

    # Act
    result = await repo.get(db_conn, created.id)

    # Assert
    assert result is not None
    assert result.id == created.id
    assert result.name == "fetch-me"


@pytest.mark.anyio
async def test_get_returns_none_when_id_does_not_exist(
    db_conn: AsyncConnection, repo: AppsRepository
):
    # Act
    result = await repo.get(db_conn, 999999)

    # Assert
    assert result is None


@pytest.mark.anyio
async def test_get_by_many_ids_returns_matching_records(
    db_conn: AsyncConnection, repo: AppsRepository
):
    # Arrange
    app_1 = await app_db_schema_factory(db_conn=db_conn, name="a")
    app_2 = await app_db_schema_factory(db_conn=db_conn, name="b")
    await app_db_schema_factory(db_conn=db_conn, name="c")

    # Act
    results = await repo.get_by_many_ids(
        db_conn, [app_1.id, app_2.id]
    )

    # Assert
    assert len(results) == 2
    returned_ids = {r.id for r in results}
    assert returned_ids == {app_1.id, app_2.id}


@pytest.mark.anyio
async def test_get_by_many_ids_returns_empty_list_when_given_empty_list(
    db_conn: AsyncConnection, repo: AppsRepository
):
    # Act
    results = await repo.get_by_many_ids(db_conn, [])

    # Assert
    assert results == []


@pytest.mark.anyio
async def test_update_returns_record_by_id(
    db_conn: AsyncConnection, repo: AppsRepository
):
    # Arrange
    created = await app_db_schema_factory(
        db_conn=db_conn, name="my-app"
    )
    update_data = UpdateSchema(id=created.id)

    # Act
    result = await repo.update(db_conn, update_data)

    # Assert
    assert result is not None
    assert result.id == created.id
    assert result.name == "my-app"


@pytest.mark.anyio
async def test_update_returns_none_when_id_does_not_exist(
    db_conn: AsyncConnection, repo: AppsRepository
):
    # Act
    result = await repo.update(db_conn, UpdateSchema(id=999999))

    # Assert
    assert result is None


@pytest.mark.anyio
async def test_get_by_slug_returns_matching_app(
    db_conn: AsyncConnection, repo: AppsRepository
):
    # Arrange
    await app_db_schema_factory(db_conn, slug="other-app")
    created = await app_db_schema_factory(
        db_conn, slug="my-unique-app"
    )

    # Act
    result = await repo.get_by_slug(db_conn, "my-unique-app")

    # Assert
    assert result is not None
    assert result.id == created.id
    assert result.slug == "my-unique-app"


@pytest.mark.anyio
async def test_get_by_slug_returns_none_when_slug_does_not_exist(
    db_conn: AsyncConnection, repo: AppsRepository
):
    # Act
    result = await repo.get_by_slug(db_conn, "nonexistent-slug")

    # Assert
    assert result is None
