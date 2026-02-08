import pytest
from sqlalchemy.ext.asyncio import AsyncConnection

from src.repositories.prompt_version import (
    PromptVersionRepository,
)
from tests.factories.app import app_db_schema_factory
from tests.factories.evaluation import evaluation_db_schema_factory
from tests.factories.prompt_version import (
    prompt_version_create_schema_factory,
    prompt_version_db_schema_factory,
)
from tests.factories.sample import sample_db_schema_factory


@pytest.fixture
def repo() -> PromptVersionRepository:
    return PromptVersionRepository()


@pytest.mark.anyio
async def test_create_returns_hash_correctly(
    db_conn: AsyncConnection,
    repo: PromptVersionRepository,
):
    # Arrange
    create_schema = prompt_version_create_schema_factory(
        content="foo"
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
    assert result.created_at is not None


@pytest.mark.anyio
async def test_get_prompt_by_sample_id(
    db_conn: AsyncConnection,
    repo: PromptVersionRepository,
):
    # Arrange
    prompt = await prompt_version_db_schema_factory(
        db_conn, content="foo"
    )
    app = await app_db_schema_factory(db_conn, prompt_id=prompt.id)
    evaluation = await evaluation_db_schema_factory(
        db_conn=db_conn, app_id=app.id
    )
    sample = await sample_db_schema_factory(
        db_conn=db_conn, evaluation_id=evaluation.id
    )

    # Act
    result = await repo.get_prompt(db_conn, sample.id)

    # Assert
    assert result is not None
    assert result.id == prompt.id


@pytest.mark.anyio
async def test_get_by_app_id(
    db_conn: AsyncConnection,
    repo: PromptVersionRepository,
):
    # Arrange
    prompt = await prompt_version_db_schema_factory(
        db_conn, content="foo"
    )
    app = await app_db_schema_factory(
        db_conn, prompt_id=prompt.id
    )

    # Act
    result = await repo.get_by_app_id(db_conn, app.id)

    # Assert
    assert result is not None
    assert result.id == prompt.id
    assert result.content == "foo"


@pytest.mark.anyio
async def test_get_by_app_id_returns_none_for_missing_app(
    db_conn: AsyncConnection,
    repo: PromptVersionRepository,
):
    # Act
    result = await repo.get_by_app_id(db_conn, 99999)

    # Assert
    assert result is None
