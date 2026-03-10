from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncConnection

from src.api.v1.response import ORJsonResponse
from src.api.v1.schemas import (
    ErrorResponse,
    JudgmentRequest,
    SampleJudgments,
)
from src.dependencies import (
    get_connection,
    judgment_commands,
    judgment_repo,
    sample_queries,
)
from src.judgment.schemas import JudgmentResult

router = APIRouter(
    prefix="/sample",
    tags=["Sample"],
    default_response_class=ORJsonResponse,
)


@router.post(
    "/{sample_id}/judgment",
    operation_id="postJudgment",
    description="Add a judgment to a sample, used for human judging",
    status_code=201,
    responses={
        404: {"model": ErrorResponse},
        400: {"model": ErrorResponse},
    },
)
async def post_sample(
    sample_id: int,
    request: JudgmentRequest,
    conn: AsyncConnection = Depends(get_connection),
) -> None:
    judgment = await judgment_repo.get_human_judgment_by_sample_id(
        conn, sample_id
    )
    if judgment is None:
        raise HTTPException(
            status_code=404,
            detail="Judgment not found",
        )
    if judgment.passed is not None:
        raise HTTPException(
            status_code=400,
            detail="Judgment already judged",
        )

    await judgment_commands.create(
        conn,
        judgment.id,
        JudgmentResult(**request.model_dump()),
    )


@router.get(
    "/{sample_id}",
    operation_id="getSampleDetail",
    responses={
        404: {"model": ErrorResponse},
    },
)
async def get_sample(
    sample_id: int,
    conn: AsyncConnection = Depends(get_connection),
) -> SampleJudgments:
    sample_judgments = await sample_queries.judgments_with_summary(
        conn, sample_id
    )
    if sample_judgments is None:
        raise HTTPException(
            status_code=404,
            detail="Sample not found",
        )
    return sample_judgments
