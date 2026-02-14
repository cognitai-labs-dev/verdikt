from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncConnection

from src.api.v1.response import ORJsonResponse
from src.api.v1.schemas import (
    ErrorResponse,
    SampleSummary,
)
from src.dependencies import (
    evaluation_queries,
    get_connection,
    sample_queries,
)

router = APIRouter(
    prefix="/evaluation",
    tags=["Evaluation"],
    default_response_class=ORJsonResponse,
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
