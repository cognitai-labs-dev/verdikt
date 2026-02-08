import pytest
from sqlalchemy.ext.asyncio import AsyncConnection

from src.repositories.prompt_version import (
    PromptVersionRepository,
)
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
