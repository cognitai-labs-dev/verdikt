from fastapi import APIRouter, HTTPException

from src.api.v1.response import ORJsonResponse
from src.api.v1.schemas import EvaluationRequest
from src.judging.schemas import JudgeResult
from src.judging.services import JudgeService

router = APIRouter(prefix="/v1", default_response_class=ORJsonResponse)
judge_service = JudgeService()


@router.post("/evaluation/{eval_id}")
async def post_evaluation(eval_id: int, request: EvaluationRequest):
    judge_id = judge_service.get_human_judge_by_eval(eval_id)
    if judge_id is None:
        raise HTTPException(status_code=400, detail="Judge type not supported")

    judge_service.save_judge(judge_id, JudgeResult(**request.model_dump()))
    return {}


#
#
# @router.get("/judge")
# async def get_judge(evaluation_run_id: int) -> list[JudgeCreateSchema]:
#     return judge_service.get_human_judges_by_run_id(evaluation_run_id)
