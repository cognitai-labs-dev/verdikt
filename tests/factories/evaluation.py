from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncConnection

from src.constants import EvaluationType
from src.repositories.evaluation import EvaluationsRepository
from src.schemas.evaluation import (
    EvaluationCreateSchema,
    EvaluationSchema,
)
from tests.utils import random_int


def evaluation_create_schema_factory(
    app_id: int | None = None,
    version: str | None = None,
    type: EvaluationType = EvaluationType.LLM_ONLY,
) -> EvaluationCreateSchema:
    return EvaluationCreateSchema(
        app_id=app_id or random_int(),
        version=version or "1.0.0",
        type=type,
    )


async def evaluation_db_schema_factory(
    db_conn: AsyncConnection | None = None,
    app_id: int | None = None,
    version: str | None = None,
    type: EvaluationType = EvaluationType.LLM_ONLY,
) -> EvaluationSchema:
    create_schema = evaluation_create_schema_factory(
        app_id=app_id,
        type=type,
        version=version,
    )
    if db_conn:
        repo = EvaluationsRepository()
        return await repo.create(db_conn, create_schema)
    else:
        now = datetime.now(timezone.utc)
        return EvaluationSchema(
            **create_schema.model_dump(),
            id=random_int(),
            created_at=now,
        )
