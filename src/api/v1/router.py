from fastapi import APIRouter, HTTPException

from src.api.v1.response import ORJsonResponse
from src.api.v1.schemas import HumanJudgeRequest
from src.constants import JudgeType
from src.judging.schemas import JudgeResult
from src.judging.services import JudgeService

router = APIRouter(prefix="/v1", default_response_class=ORJsonResponse)
judge_service = JudgeService()


@router.post("/judge/{judge_id}")
async def human_judge(judge_id: int, request: HumanJudgeRequest):
    if judge_service.get_judge_type(judge_id) != JudgeType.HUMAN:
        raise HTTPException(status_code=400, detail="Judge type not supported")

    judge_service.save_judge(judge_id, JudgeResult(**request.model_dump()))
    return {}
