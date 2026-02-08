from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncConnection

from src.constants import EvaluationType
from src.repositories.evaluation import EvaluationsRepository
from src.schemas.evaluation import (
    EvaluationCreateSchema,
    EvaluationSchema,
)
from tests.factories.prompt_version import (
    prompt_version_db_schema_factory,
)
from tests.utils import random_int


def evaluation_create_schema_factory(
    app_id: int | None = None,
    version: str | None = None,
    type: EvaluationType = EvaluationType.LLM_ONLY,
    prompt_version_id: int | None = None,
) -> EvaluationCreateSchema:
    return EvaluationCreateSchema(
        app_id=app_id or random_int(),
        version=version or "1.0.0",
        type=type,
        prompt_version_id=prompt_version_id or 1,
    )


async def evaluation_db_schema_factory(
    db_conn: AsyncConnection | None = None,
    app_id: int | None = None,
    version: str | None = None,
    type: EvaluationType = EvaluationType.LLM_ONLY,
    prompt_version_id: int | None = None,
) -> EvaluationSchema:
    if prompt_version_id is None:
        prompt = await prompt_version_db_schema_factory(db_conn)
        prompt_version_id = prompt.id

    create_schema = evaluation_create_schema_factory(
        app_id=app_id,
        type=type,
        version=version,
        prompt_version_id=prompt_version_id,
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
