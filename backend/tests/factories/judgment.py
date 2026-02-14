from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncConnection

from src.constants import JudgmentStatus, JudgmentType
from src.repositories.judgment import JudgmentRepository
from src.schemas.judgment import JudgmentCreateSchema, JudgmentSchema
from tests.utils import random_int


def judgment_create_schema_factory(
    sample_id: int = 1,
    judgment_type: JudgmentType = JudgmentType.LLM,
    judgment_model: str = "gpt-4o-mini",
    status: JudgmentStatus = JudgmentStatus.PENDING,
    reasoning: str | None = None,
    passed: bool | None = None,
    input_tokens: int | None = None,
    output_tokens: int | None = None,
    input_tokens_cost: float | None = None,
    output_tokens_cost: float | None = None,
) -> JudgmentCreateSchema:
    return JudgmentCreateSchema(
        sample_id=sample_id,
        judgment_type=judgment_type,
        judgment_model=judgment_model,
        status=status,
        reasoning=reasoning,
        passed=passed,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        input_tokens_cost=input_tokens_cost,
        output_tokens_cost=output_tokens_cost,
    )


async def judgment_db_schema_factory(
    db_conn: AsyncConnection | None = None,
    sample_id: int = 1,
    judgment_type: JudgmentType = JudgmentType.LLM,
    judgment_model: str = "gpt-4o-mini",
    status: JudgmentStatus = JudgmentStatus.PENDING,
    reasoning: str | None = None,
    passed: bool | None = None,
    input_tokens: int | None = None,
    output_tokens: int | None = None,
    input_tokens_cost: float | None = None,
    output_tokens_cost: float | None = None,
) -> JudgmentSchema:
    create_schema = judgment_create_schema_factory(
        sample_id=sample_id,
        judgment_type=judgment_type,
        judgment_model=judgment_model,
        status=status,
        reasoning=reasoning,
        passed=passed,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        input_tokens_cost=input_tokens_cost,
        output_tokens_cost=output_tokens_cost,
    )
    if db_conn:
        repo = JudgmentRepository()
        return await repo.create(db_conn, create_schema)
    else:
        now = datetime.now(timezone.utc)
        return JudgmentSchema(
            **create_schema.model_dump(),
            id=random_int(),
            created_at=now,
            updated_at=now,
        )
