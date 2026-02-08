from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncConnection

from src.api.v1.response import ORJsonResponse
from src.api.v1.schemas import (
    AppDatasetsRequest,
    AppRequest,
    ErrorResponse,
    EvaluationRequest,
)
from src.dependencies import (
    app_dataset_repo,
    app_repo,
    evaluation_commands,
    get_connection,
)
from src.evaluation.schemas import EvaluationSchema
from src.schemas.app import AppCreateSchema, AppSchema
from src.schemas.app_dataset import (
    AppDatasetCreateSchema,
    AppDatasetSchema,
)

router = APIRouter(
    prefix="/app",
    tags=["App"],
    default_response_class=ORJsonResponse,
)


@router.get(
    "/{app_id}",
    operation_id="getApp",
    responses={
        404: {"model": ErrorResponse},
    },
)
async def get_app(
    app_id: int,
    conn: AsyncConnection = Depends(get_connection),
) -> AppSchema:
    app = await app_repo.get(conn, app_id)
    if not app:
        raise HTTPException(status_code=404, detail="app not found")
    return app


@router.get("", operation_id="getApps")
async def get_apps(
    conn: AsyncConnection = Depends(get_connection),
) -> list[AppSchema]:
    return await app_repo.get_many(conn)


@router.post(
    "",
    operation_id="postApp",
    status_code=201,
)
async def post_app(
    request: AppRequest,
    conn: AsyncConnection = Depends(get_connection),
) -> None:
    await app_repo.create(conn, AppCreateSchema(name=request.name))


@router.delete(
    "/{app_id}",
    operation_id="deleteApp",
    status_code=204,
    responses={
        404: {"model": ErrorResponse},
    },
)
async def delete_app(
    app_id: int,
    conn: AsyncConnection = Depends(get_connection),
) -> None:
    deleted = await app_repo.delete(conn, app_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="App not found")


@router.post(
    "/{app_id}/datasets",
    operation_id="postAppDatasets",
    status_code=201,
    responses={
        404: {"model": ErrorResponse},
    },
)
async def post_app_datasets(
    app_id: int,
    request: AppDatasetsRequest,
    conn: AsyncConnection = Depends(get_connection),
) -> None:
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


@router.get(
    "/{app_id}/datasets",
    operation_id="getAppDatasets",
    responses={
        404: {"model": ErrorResponse},
    },
)
async def get_app_datasets(
    app_id: int,
    conn: AsyncConnection = Depends(get_connection),
) -> list[AppDatasetSchema]:
    app = await app_repo.get(conn, app_id)
    if app is None:
        raise HTTPException(status_code=404, detail="App not found")

    return await app_dataset_repo.get_many_by_app_id(conn, app_id)


@router.post(
    "/{app_id}/evaluation",
    operation_id="postAppEvaluation",
    status_code=201,
    responses={
        400: {"model": ErrorResponse},
    },
)
async def post_app_evaluation(
    app_id: int,
    request: EvaluationRequest,
    conn: AsyncConnection = Depends(get_connection),
) -> None:
    try:
        await evaluation_commands.create(
            conn,
            EvaluationSchema(app_id=app_id, **request.model_dump()),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
