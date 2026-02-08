from sqlalchemy.ext.asyncio import AsyncConnection

from src.repositories.app_dataset import AppDatasetRepository
from src.schemas.app_dataset import (
    AppDatasetCreateSchema,
    AppDatasetSchema,
)


async def app_dataset_db_schema_factory(
    db_conn: AsyncConnection,
    app_id: int,
    question: str = "What is 2+2?",
    human_answer: str = "4",
) -> AppDatasetSchema:
    """Create an app dataset record in the database and return it."""
    repo = AppDatasetRepository()
    return await repo.create(
        db_conn,
        AppDatasetCreateSchema(
            question=question,
            human_answer=human_answer,
            app_id=app_id,
        ),
    )
