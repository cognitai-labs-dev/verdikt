from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncConnection

from src.api.v1.response import ORJsonResponse
from src.api.v1.schemas import (
    AppDatasetsRequest,
    AppRequest,
    ErrorResponse,
    EvaluationRequest,
    EvaluationSummary,
    PromptVersionSummary,
)
from src.constants import EvaluationType
from src.dependencies import (
    app_commands,
    app_dataset_repo,
    app_repo,
    evaluation_commands,
    evaluation_queries,
    evaluation_repo,
    get_connection,
    prompt_queries,
    prompt_version_repo,
)
from src.evaluation.schemas import EvaluationSchema
from src.schemas.app import AppSchema, AppUpdateSchema
from src.schemas.app_dataset import (
    AppDatasetCreateSchema,
    AppDatasetSchema,
)
from src.schemas.prompt_version import (
    PromptVersionCreateSchema,
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
    await app_commands.create(conn, request.name)


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


class PromptRequest(BaseModel):
    content: str = Field(
        description="Prompt content",
    )


class UpdateCurrentPromptRequest(BaseModel):
    prompt_id: int = Field(
        description="Prompt version ID to set as current",
    )


@router.get(
    "/{app_id}/prompt",
    operation_id="getAppPrompt",
    responses={
        404: {"model": ErrorResponse},
    },
)
async def get_app_prompts(
    app_id: int,
    conn: AsyncConnection = Depends(get_connection),
) -> list[PromptVersionSummary]:
    app = await app_repo.get(conn, app_id)
    if app is None:
        raise HTTPException(status_code=404, detail="App not found")

    return await prompt_queries.prompts_summaries_by_app(conn, app_id)


@router.post(
    "/{app_id}/prompt",
    operation_id="postAppPrompt",
    status_code=201,
    responses={
        404: {"model": ErrorResponse},
    },
)
async def post_app_prompt(
    app_id: int,
    request: PromptRequest,
    conn: AsyncConnection = Depends(get_connection),
) -> PromptVersionSummary:
    app = await app_repo.get(conn, app_id)
    if app is None:
        raise HTTPException(status_code=404, detail="App not found")

    new_prompt = await prompt_version_repo.create(
        conn,
        PromptVersionCreateSchema(
            app_id=app_id,
            content=request.content,
        ),
    )
    return (
        await prompt_queries.prompts_summaries(conn, [new_prompt])
    )[0]


@router.patch(
    "/{app_id}",
    operation_id="patchApp",
    responses={
        404: {"model": ErrorResponse},
    },
)
async def patch_app(
    app_id: int,
    request: UpdateCurrentPromptRequest,
    conn: AsyncConnection = Depends(get_connection),
) -> AppSchema:
    app = await app_repo.get(conn, app_id)
    if app is None:
        raise HTTPException(status_code=404, detail="App not found")

    prompt = await prompt_version_repo.get(conn, request.prompt_id)
    if prompt is None:
        raise HTTPException(
            status_code=404,
            detail="Prompt version not found",
        )

    updated = await app_repo.update(
        conn,
        AppUpdateSchema(
            id=app_id,
            current_prompt_version_id=request.prompt_id,
        ),
    )
    if updated is None:
        raise HTTPException(status_code=404, detail="App not found")

    return updated


@router.get(
    "/{app_id}/evaluation/summary",
    operation_id="getEvaluationsSummaries",
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
