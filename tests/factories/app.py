from sqlalchemy.ext.asyncio import AsyncConnection

from src.repositories.apps import AppsRepository
from src.schemas.app import AppCreateSchema, AppSchema
from tests.factories.prompt_version import (
    prompt_version_db_schema_factory,
)


def app_create_schema_factory(
    prompt_version_id: int,
    name: str = "test-app",
) -> AppCreateSchema:
    return AppCreateSchema(
        name=name, current_prompt_version_id=prompt_version_id
    )


async def app_db_schema_factory(
    db_conn: AsyncConnection,
    name: str = "test-app",
    prompt_id: int | None = None,
) -> AppSchema:
    """Create an app record in the database and return it."""
    if not prompt_id:
        prompt = await prompt_version_db_schema_factory(db_conn)
        prompt_id = prompt.id
    repo = AppsRepository()
    return await repo.create(
        db_conn,
        AppCreateSchema(
            name=name, current_prompt_version_id=prompt_id
        ),
    )
