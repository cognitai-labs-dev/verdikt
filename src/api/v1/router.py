from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncConnection

from src.api.v1.response import ORJsonResponse
from src.api.v1.schemas import (
    AppDatasetsRequest,
    AppRequest,
    EvaluationSummary,
    JudgmentRequest,
    SampleJudgements,
    SampleSummary,
)
from src.constants import EvaluationType
from src.dependencies import (
    app_dataset_repo,
    app_repo,
    evaluation_queries,
    evaluation_repo,
    get_connection,
    judgement_commands,
    judgment_repo,
    sample_queries,
)
from src.judgement.schemas import JudgmentResult
from src.schemas.app import AppCreateSchema
from src.schemas.app_dataset import (
    AppDatasetCreateSchema,
    AppDatasetSchema,
)

router = APIRouter(
    prefix="/v1", default_response_class=ORJsonResponse
)


@router.post(
    "/sample/{sample_id}/judgment",
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


@router.get("/sample/{sample_id}", operation_id="getSampleDetail")
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


@router.get(
    "/evaluation/summary", operation_id="getEvaluationsSummaries"
)
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
    "/evaluation/{evaluation_id}/samples/summary",
    operation_id="getSamplesSummaries",
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
            status_code=404, detail="Evaluation not found"
        )

    return await sample_queries.summary_by_eval_ids(
        conn, [evaluation_id], evaluation.type
    )


@router.post("/app", operation_id="postApp")
async def post_app(
    request: AppRequest,
    conn: AsyncConnection = Depends(get_connection),
):
    await app_repo.create(conn, AppCreateSchema(name=request.name))


@router.post("/app/{app_id}/datasets", operation_id="postAppDatasets")
async def post_app_datasets(
    app_id: int,
    request: AppDatasetsRequest,
    conn: AsyncConnection = Depends(get_connection),
):
    app = await app_repo.get(conn, app_id)
    if app is None:
        raise HTTPException(status_code=404, detail="App not found")

    items = [
        AppDatasetCreateSchema(
            question=d.question,
            human_answer=d.human_answer,
            app_id=app_id,
        )
        for d in request.datasets
    ]
    await app_dataset_repo.create_many(conn, items)


@router.get("/app/{app_id}/datasets", operation_id="getAppDatasets")
async def get_app_datasets(
    app_id: int,
    conn: AsyncConnection = Depends(get_connection),
) -> list[AppDatasetSchema]:
    app = await app_repo.get(conn, app_id)
    if app is None:
        raise HTTPException(status_code=404, detail="App not found")

    return await app_dataset_repo.get_many_by_app_id(conn, app_id)
