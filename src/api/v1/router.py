from fastapi import APIRouter, HTTPException

from src.api.v1.response import ORJsonResponse
from src.api.v1.schemas import JudgmentRequest
from src.crud.sample import samples_crud
from src.judging.schemas import JudgmentResult
from src.judging.services import JudgmentService
from src.schemas.sample import SampleSchema

router = APIRouter(prefix="/v1", default_response_class=ORJsonResponse)
judgment_service = JudgmentService()


@router.post("/sample/{sample_id}/judgment")
async def post_judgment(sample_id: int, request: JudgmentRequest):
    judgment_id = judgment_service.get_human_judgment_by_sample(sample_id)
    if judgment_id is None:
        raise HTTPException(status_code=400, detail="Judgment type not supported")

    judgment_service.save_judgment(judgment_id, JudgmentResult(**request.model_dump()))
    return {}


@router.get("/sample")
async def get_samples(evaluation_id: int) -> list[SampleSchema]:
    return samples_crud.get_many_by_evaluation(evaluation_id)
