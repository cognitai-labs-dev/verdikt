from fastapi import APIRouter, HTTPException

from src.api.v1.response import ORJsonResponse
from src.api.v1.schemas import (
    EvaluationSummary,
    JudgmentRequest,
    SampleJudgements,
    SampleSummary,
)
from src.constants import EvaluationType
from src.evaluation.queries import EvaluationQueries
from src.judgement.commands import JudgementCommands
from src.judgement.schemas import JudgmentResult
from src.repositories.evaluation import (
    evaluations_repository,
)
from src.repositories.judgment import judgment_repository
from src.sample.queries import SampleQueries

router = APIRouter(
    prefix="/v1", default_response_class=ORJsonResponse
)
judgment_commands = JudgementCommands()
sample_queries = SampleQueries()
evaluation_queries = EvaluationQueries()


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

    judgment_commands.create(
        judgment.id, JudgmentResult(**request.model_dump())
    )


@router.get("/sample/{sample_id}", operation_id="getSampleDetail")
async def get_sample(sample_id: int) -> SampleJudgements:
    sample_judgements = sample_queries.judgements_with_summary(
        sample_id
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

    return evaluation_queries.evaluation_summaries_by_eval_ids(
        evaluations, eval_type
    )


@router.get(
    "/evaluation/{evaluation_id}/samples/summary",
    operation_id="getSamplesSummaries",
)
async def get_evaluation_samples(
    evaluation_id: int,
) -> list[SampleSummary]:
    evaluation = evaluations_repository.get(evaluation_id)
    if evaluation is None:
        raise HTTPException(
            status_code=404, detail="Evaluation not found"
        )

    return sample_queries.summary_by_eval_ids(
        [evaluation_id], evaluation.type
    )
