from sqlalchemy.ext.asyncio import AsyncConnection

from src.repositories.apps import AppsRepository
from src.schemas.app import (
    AppCreateSchema,
    AppSchema,
)


def app_create_schema_factory(
    name: str = "test-app",
    prompt_version_id: int | None = None,
) -> AppCreateSchema:
    return AppCreateSchema(
        name=name,
        current_prompt_version_id=prompt_version_id,
    )


async def app_db_schema_factory(
    db_conn: AsyncConnection,
    name: str = "test-app",
) -> AppSchema:
    """Create an app record in the database."""
    repo = AppsRepository()
    app = await repo.create(
        db_conn,
        AppCreateSchema(name=name),
    )
    return app
