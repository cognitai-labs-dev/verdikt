from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncConnection

from src.repositories.sample import SamplesRepository
from src.schemas.sample import SampleCreateSchema, SampleSchema
from tests.utils import random_int


def sample_create_schema_factory(
    evaluation_id: int = 1,
    question: str = "What is 2+2?",
    human_answer: str = "4",
    app_answer: str = "The answer is 4.",
    app_cost: float | None = None,
    metadata: dict[str, Any] | None = None,
) -> SampleCreateSchema:
    return SampleCreateSchema(
        evaluation_id=evaluation_id,
        question=question,
        human_answer=human_answer,
        app_answer=app_answer,
        app_cost=app_cost,
        metadata=metadata,
    )


async def sample_db_schema_factory(
    db_conn: AsyncConnection | None = None,
    evaluation_id: int = 1,
    question: str = "What is 2+2?",
    human_answer: str = "4",
    app_answer: str = "The answer is 4.",
    app_cost: float | None = None,
    metadata: dict[str, Any] | None = None,
) -> SampleSchema:
    create_schema = sample_create_schema_factory(
        evaluation_id=evaluation_id,
        question=question,
        human_answer=human_answer,
        app_answer=app_answer,
        app_cost=app_cost,
        metadata=metadata,
    )
    if db_conn:
        repo = SamplesRepository()
        return await repo.create(db_conn, create_schema)
    else:
        now = datetime.now(timezone.utc)
        return SampleSchema(
            **create_schema.model_dump(),
            id=random_int(),
            created_at=now,
        )
