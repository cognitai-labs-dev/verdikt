from pydantic import BaseModel

from src.schemas.judgment import JudgmentSchema
from src.schemas.sample import SampleSchema


class JudgmentRequest(BaseModel):
    reasoning: str
    passed: bool
    score: int


class EvaluationSummaryResponse(BaseModel):
    """
    TODO: for only for 1 LLM type, later expand to a map of llm statistics
    TODO: Adjust for FE needs
    """

    id: int
    samples_count: int

    llm_judgments_count: int
    llm_judgments_count_passed: int

    average_llm_score: float

    average_human_score: float
    agreement_ratio: float


class SampleSummary(SampleSchema):
    human_judgment_passed: bool | None
    llm_judgments_count_passed: int
    llm_judgments_count: int


class SampleDetail(SampleSchema):
    human_judgment: JudgmentSchema
    llm_judgements: list[JudgmentSchema]
