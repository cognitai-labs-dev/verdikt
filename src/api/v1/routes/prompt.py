from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncConnection

from src.api.v1.response import ORJsonResponse
from src.dependencies import get_connection

router = APIRouter(
    prefix="/prompt",
    tags=["Prompt"],
    default_response_class=ORJsonResponse,
)


@router.get("/{prompt_id}/samples/summary")
async def prompt_samples_summary(
    prompt_id: int, conn: AsyncConnection = Depends(get_connection)
):
    pass
