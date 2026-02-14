from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncConnection

from src.api.v1.response import ORJsonResponse
from src.api.v1.schemas import (
    ErrorResponse,
    SampleSummary,
)
from src.constants import JudgmentType
from src.dependencies import (
    evaluation_queries,
    get_connection,
    sample_queries,
    sample_repo,
)
from src.schemas.sample import SampleWithJudgmentSchema

router = APIRouter(
    prefix="/evaluation",
    tags=["Evaluation"],
    default_response_class=ORJsonResponse,
)


@router.get(
    "/{evaluation_id}/sample/summary",
    operation_id="getSamplesSummaries",
    responses={
        404: {"model": ErrorResponse},
    },
)
async def get_evaluation_samples_summaries(
    evaluation_id: int,
    conn: AsyncConnection = Depends(get_connection),
) -> list[SampleSummary]:
    evaluation = (
        await evaluation_queries.sample_queries.evaluation.get(
            conn, evaluation_id
        )
    )
    if evaluation is None:
        raise HTTPException(
            status_code=404,
            detail="Evaluation not found",
        )

    return await sample_queries.summary_by_eval_ids(
        conn, [evaluation_id], evaluation.type
    )


@router.get(
    "/{evaluation_id}/sample/judgment",
    operation_id="getEvaluationSamples",
)
async def get_evaluation_samples(
    evaluation_id: int,
    judgment_type: JudgmentType = JudgmentType.HUMAN,
    conn: AsyncConnection = Depends(get_connection),
) -> list[SampleWithJudgmentSchema]:
    return await sample_repo.get_many_by_evaluation_with_judgements(
        conn, evaluation_id, judgment_type
    )
