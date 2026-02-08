from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncConnection

from src.api.v1.response import ORJsonResponse
from src.api.v1.schemas import (
    ErrorResponse,
    EvaluationSummary,
    SampleSummary,
)
from src.constants import EvaluationType
from src.dependencies import (
    evaluation_queries,
    evaluation_repo,
    get_connection,
    sample_queries,
)

router = APIRouter(
    prefix="/evaluation",
    tags=["Evaluation"],
    default_response_class=ORJsonResponse,
)


@router.get("/summary", operation_id="getEvaluationsSummaries")
async def get_evaluations(
    app_id: int,
    eval_type: EvaluationType,
    conn: AsyncConnection = Depends(get_connection),
) -> list[EvaluationSummary]:
    evaluations = await evaluation_repo.get_many_by_app_id(
        conn, app_id, eval_type
    )
    if len(evaluations) == 0:
        return []

    return await evaluation_queries.evaluation_summaries_by_eval_ids(
        conn, evaluations, eval_type
    )


@router.get(
    "/{evaluation_id}/samples/summary",
    operation_id="getSamplesSummaries",
    responses={
        404: {"model": ErrorResponse},
    },
)
async def get_evaluation_samples(
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
