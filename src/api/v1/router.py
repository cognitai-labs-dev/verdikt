from fastapi import APIRouter, HTTPException

from src.api.v1.response import ORJsonResponse
from src.api.v1.schemas import (
    JudgmentRequest,
    SampleSummaryResponse,
)
from src.constants import EvaluationType
from src.crud.evaluation import evaluations_crud
from src.judging.schemas import JudgmentResult
from src.api.v1.schemas import SampleDetail
from src.judging.services import JudgmentService
from src.schemas.evaluation import EvaluationSchema

router = APIRouter(prefix="/v1", default_response_class=ORJsonResponse)
judgment_service = JudgmentService()


@router.post("/sample/{sample_id}/judgment", operation_id="postJudgment")
async def post_sample(sample_id: int, request: JudgmentRequest):
    judgment = judgment_service.get_human_judgment_by_sample(sample_id)
    if judgment is None:
        raise HTTPException(status_code=400, detail="Judgment not found")
    if judgment.passed is not None:
        raise HTTPException(status_code=400, detail="Judgment already judged")

    judgment_service.save_judgment(judgment.id, JudgmentResult(**request.model_dump()))


@router.get("/sample/{sample_id}", operation_id="getSampleDetail")
async def get_sample(sample_id: int) -> SampleDetail:
    return judgment_service.sample_judgment_detail(sample_id)


@router.get("/evaluations", operation_id="getEvaluations")
async def get_evaluations(
    app_id: str, eval_type: EvaluationType
) -> list[EvaluationSchema]:
    return evaluations_crud.get_many_by_app_id(app_id, eval_type)


@router.get("/evaluation/{evaluation_id}/samples", operation_id="getSampleSummaries")
async def get_evaluation_samples(
    evaluation_id: int,
) -> SampleSummaryResponse:
    evaluation = evaluations_crud.get(evaluation_id)
    if evaluation is None:
        raise HTTPException(status_code=404, detail="Evaluation not found")

    if evaluation.type == EvaluationType.HUMAN_AND_LLM:
        return SampleSummaryResponse(
            evaluation_type=EvaluationType.HUMAN_AND_LLM,
            samples=judgment_service.sample_judgments_summary_human(evaluation_id),
        )
    else:
        return SampleSummaryResponse(
            evaluation_type=EvaluationType.LLM_ONLY,
            samples=judgment_service.sample_judgments_summary_llm_only(evaluation_id),
        )


# @router.get("/evaluation/{evaluation_id}/summary")
# async def get_evaluation_summary(evaluation_id: int) -> EvaluationSummaryResponse:
#     return
