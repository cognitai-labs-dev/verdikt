from sqlalchemy.ext.asyncio import AsyncConnection

from src.repositories.apps import AppsRepository
from src.schemas.app import AppCreateSchema, AppSchema


async def app_db_schema_factory(
    db_conn: AsyncConnection,
    name: str = "test-app",
) -> AppSchema:
    """Create an app record in the database and return it."""
    repo = AppsRepository()
    return await repo.create(db_conn, AppCreateSchema(name=name))
