from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncConnection

from src.repositories.prompt_version import (
    PromptVersionRepository,
)
from src.schemas.prompt_version import (
    PromptVersionCreateSchema,
    PromptVersionSchema,
)
from tests.utils import random_int, random_word


def prompt_version_create_schema_factory(
    content: str | None = None,
) -> PromptVersionCreateSchema:
    return PromptVersionCreateSchema(content=content or random_word())


async def prompt_version_db_schema_factory(
    db_conn: AsyncConnection | None = None,
    content: str | None = None,
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
