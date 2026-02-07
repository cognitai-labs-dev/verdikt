from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncConnection

from src.api.v1.response import ORJsonResponse
from src.api.v1.schemas import (
    AppDatasetsRequest,
    AppRequest,
    EvaluationRequest,
)
from src.dependencies import (
    app_dataset_repo,
    app_repo,
    evaluation_commands,
    get_connection,
)
from src.evaluation.schemas import EvaluationSchema
from src.schemas.app import AppCreateSchema
from src.schemas.app_dataset import (
    AppDatasetCreateSchema,
    AppDatasetSchema,
)

router = APIRouter(
    prefix="/app",
    tags=["App"],
    default_response_class=ORJsonResponse,
)


@router.post("", operation_id="postApp")
async def post_app(
    request: AppRequest,
    conn: AsyncConnection = Depends(get_connection),
):
    await app_repo.create(conn, AppCreateSchema(name=request.name))


@router.delete("/{app_id}", operation_id="deleteApp")
async def delete_app(
    app_id: int,
    conn: AsyncConnection = Depends(get_connection),
):
    await app_repo.delete(conn, app_id)


@router.post("/{app_id}/datasets", operation_id="postAppDatasets")
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


@router.get("/{app_id}/datasets", operation_id="getAppDatasets")
async def get_app_datasets(
    app_id: int,
    conn: AsyncConnection = Depends(get_connection),
) -> list[AppDatasetSchema]:
    app = await app_repo.get(conn, app_id)
    if app is None:
        raise HTTPException(status_code=404, detail="App not found")

    return await app_dataset_repo.get_many_by_app_id(conn, app_id)


@router.post("/{app_id}/evaluation", operation_id="postAppEvaluation")
async def post_app_evaluation(
    app_id: int,
    request: EvaluationRequest,
    conn: AsyncConnection = Depends(get_connection),
):
    try:
        await evaluation_commands.create(
            conn,
            EvaluationSchema(app_id=app_id, **request.model_dump()),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
