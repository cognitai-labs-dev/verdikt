from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncConnection

from src.repositories.prompt_version import (
    PromptVersionRepository,
)
from src.schemas.prompt_version import (
    PromptVersionCreateSchema,
    PromptVersionSchema,
)
from tests.utils import random_int


def prompt_version_create_schema_factory(
    content: str = "You are a helpful assistant.",
) -> PromptVersionCreateSchema:
    return PromptVersionCreateSchema(content=content)


async def prompt_version_db_schema_factory(
    db_conn: AsyncConnection | None = None,
    content: str = "You are a helpful assistant.",
) -> PromptVersionSchema:
    create_schema = prompt_version_create_schema_factory(
        content=content
    )
    if db_conn:
        repo = PromptVersionRepository()
        return await repo.create(db_conn, create_schema)
    else:
        now = datetime.now(timezone.utc)
        return PromptVersionSchema(
            **create_schema.model_dump(),
            id=random_int(),
            created_at=now,
        )
