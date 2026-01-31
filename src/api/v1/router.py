from fastapi import APIRouter, HTTPException

from src.api.v1.response import ORJsonResponse
from src.api.v1.schemas import (
    EvaluationSummary,
    JudgmentRequest,
    SampleJudgements,
    SampleSummaryResponse,
)
from src.constants import EvaluationType
from src.evaluation.statistics import (
    EvaluationStatisticsService,
)
from src.judging.schemas import JudgmentResult
from src.judging.services import JudgmentService
from src.judging.statistics import (
    JudgementStatisticsService,
)
from src.repositories.evaluation import (
    evaluations_repository,
)
from src.repositories.judgment import judgment_repository

router = APIRouter(
    prefix="/v1", default_response_class=ORJsonResponse
)
judgment_service = JudgmentService()
judgment_stats_service = JudgementStatisticsService()
eval_stats_service = EvaluationStatisticsService(
    judgment_stats_service
)


@router.post(
    "/sample/{sample_id}/judgment",
    operation_id="postJudgment",
)
async def post_sample(sample_id: int, request: JudgmentRequest):
    judgment = judgment_repository.get_human_judgement_by_sample_id(
        sample_id
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

    judgment_service.save_judgment(
        judgment.id, JudgmentResult(**request.model_dump())
    )


@router.get("/sample/{sample_id}", operation_id="getSampleDetail")
async def get_sample(sample_id: int) -> SampleJudgements:
    sample_judgements = (
        judgment_stats_service.sample_judgements_with_summary(
            sample_id
        )
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
    app_id: str, eval_type: EvaluationType
) -> list[EvaluationSummary]:
    evaluations = evaluations_repository.get_many_by_app_id(
        app_id, eval_type
    )
    if len(evaluations) == 0:
        return []

    return eval_stats_service.evaluation_summaries_by_eval_ids(
        evaluations, eval_type
    )


@router.get(
    "/evaluation/{evaluation_id}/samples/summary",
    operation_id="getSamplesSummaries",
)
async def get_evaluation_samples(
    evaluation_id: int,
) -> SampleSummaryResponse:
    evaluation = evaluations_repository.get(evaluation_id)
    if evaluation is None:
        raise HTTPException(
            status_code=404, detail="Evaluation not found"
        )

    return SampleSummaryResponse(
        evaluation_type=evaluation.type,
        samples=judgment_stats_service.samples_summary_by_eval_ids(
            [evaluation_id], evaluation.type
        ),
    )
