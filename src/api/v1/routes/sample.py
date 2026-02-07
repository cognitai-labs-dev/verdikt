from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncConnection

from src.api.v1.response import ORJsonResponse
from src.api.v1.schemas import (
    JudgmentRequest,
    SampleJudgements,
)
from src.dependencies import (
    get_connection,
    judgement_commands,
    judgment_repo,
    sample_queries,
)
from src.judgement.schemas import JudgmentResult

router = APIRouter(
    prefix="/sample",
    tags=["Sample"],
    default_response_class=ORJsonResponse,
)


@router.post(
    "/{sample_id}/judgment",
    operation_id="postJudgment",
)
async def post_sample(
    sample_id: int,
    request: JudgmentRequest,
    conn: AsyncConnection = Depends(get_connection),
):
    judgment = await judgment_repo.get_human_judgement_by_sample_id(
        conn, sample_id
    )
    if judgment is None:
        raise HTTPException(
            status_code=404, detail="Judgment not found"
        )
    if judgment.passed is not None:
        raise HTTPException(
            status_code=400,
            detail="Judgment already judged",
        )

    await judgement_commands.create(
        conn,
        judgment.id,
        JudgmentResult(**request.model_dump()),
    )


@router.get("/{sample_id}", operation_id="getSampleDetail")
async def get_sample(
    sample_id: int,
    conn: AsyncConnection = Depends(get_connection),
) -> SampleJudgements:
    sample_judgements = await sample_queries.judgements_with_summary(
        conn, sample_id
    )
    if sample_judgements is None:
        raise HTTPException(
            status_code=404, detail="Sample not found"
        )
    return sample_judgements
