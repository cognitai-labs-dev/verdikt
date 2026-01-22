from fastapi import APIRouter

from src.api.v1.response import ORJsonResponse
from src.api.v1.schemas import HumanJudgeRequest

router = APIRouter(prefix="/v1", default_response_class=ORJsonResponse)


@router.post("/human-judge")
async def human_judge(request: HumanJudgeRequest):
    # TODO: add call to service
    pass
