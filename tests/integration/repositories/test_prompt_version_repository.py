import pytest
from sqlalchemy.ext.asyncio import AsyncConnection

from src.repositories.prompt_version import (
    PromptVersionRepository,
)
from tests.factories.app import app_db_schema_factory
from tests.factories.prompt_version import (
    prompt_version_create_schema_factory,
)


@pytest.fixture
def repo() -> PromptVersionRepository:
    return PromptVersionRepository()


@pytest.mark.anyio
async def test_create_returns_hash_correctly(
    db_conn: AsyncConnection,
    repo: PromptVersionRepository,
):
    # Arrange
    app = await app_db_schema_factory(db_conn)
    create_schema = prompt_version_create_schema_factory(
        app_id=app.id,
        content="foo",
    )

    # Act
    result = await repo.create(db_conn, create_schema)

    # Assert
    assert result.id is not None
    assert (
        result.hash
        == "2c26b46b68ffc68ff99b453c1d30413413422d706483bfa0f98a5e886266e7ae"
    )
    assert result.content == create_schema.content
    assert result.app_id == app.id
    assert result.created_at is not None


@pytest.mark.anyio
async def test_get_many_by_app_id_returns_prompts_for_given_app(
    db_conn: AsyncConnection,
    repo: PromptVersionRepository,
):
    # Arrange
    app = await app_db_schema_factory(db_conn)
    other_app = await app_db_schema_factory(
        db_conn, name="other-app"
    )

    await repo.create(
        db_conn,
        prompt_version_create_schema_factory(
            app_id=app.id, content="prompt-1"
        ),
    )
    await repo.create(
        db_conn,
        prompt_version_create_schema_factory(
            app_id=app.id, content="prompt-2"
        ),
    )
    await repo.create(
        db_conn,
        prompt_version_create_schema_factory(
            app_id=other_app.id, content="prompt-3"
        ),
    )

    # Act
    results = await repo.get_many_by_app_id(
        db_conn, app.id
    )

    # Assert
    assert len(results) == 2
    contents = {r.content for r in results}
    assert contents == {"prompt-1", "prompt-2"}


@pytest.mark.anyio
async def test_get_many_by_app_id_returns_empty_list_when_no_prompts(
    db_conn: AsyncConnection,
    repo: PromptVersionRepository,
):
    # Arrange
    app = await app_db_schema_factory(db_conn)

    # Act
    results = await repo.get_many_by_app_id(
        db_conn, app.id
    )

    # Assert
    assert results == []
