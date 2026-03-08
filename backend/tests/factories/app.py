import itertools

from sqlalchemy.ext.asyncio import AsyncConnection

from src.repositories.apps import AppsRepository
from src.schemas.app import (
    AppCreateSchema,
    AppSchema,
)

_counter = itertools.count(1)


def _unique_slug(base: str) -> str:
    return f"{base}-{next(_counter)}"


def app_create_schema_factory(
    name: str = "test-app",
    slug: str | None = None,
    prompt_version_id: int | None = None,
) -> AppCreateSchema:
    return AppCreateSchema(
        name=name,
        slug=slug or _unique_slug("test-app"),
        current_prompt_version_id=prompt_version_id,
    )


async def app_db_schema_factory(
    db_conn: AsyncConnection,
    name: str = "test-app",
    slug: str | None = None,
) -> AppSchema:
    """Create an app record in the database."""
    repo = AppsRepository()
    app = await repo.create(
        db_conn,
        AppCreateSchema(
            name=name,
            slug=slug or _unique_slug(name),
        ),
    )
    return app
