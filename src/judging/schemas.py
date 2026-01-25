from typing import NamedTuple

from pydantic import BaseModel

from src.schemas.judgment import JudgmentSchema
from src.schemas.sample import SampleSchema


class LLMJudgmentConfig(NamedTuple):
    provider: str
    model: str


class JudgmentResult(BaseModel):
    reasoning: str
    passed: bool
    score: int


class PricingSchema(BaseModel):
    input_tokens: int
    output_tokens: int
    input_tokens_cost: float
    output_tokens_cost: float


class SampleSummary(SampleSchema):
    human_judgment_passed: bool | None
    llm_judgments_count_passed: int
    llm_judgments_count: int


class SampleDetail(SampleSchema):
    human_judgment: JudgmentSchema | None
    llm_judgements: list[JudgmentSchema]
