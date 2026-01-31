from pydantic import BaseModel, Field

from src.constants import EvaluationType
from src.schemas.judgment import JudgmentSchema
from src.schemas.sample import SampleSchema


class JudgmentRequest(BaseModel):
    reasoning: str
    passed: bool


class SampleSummary(SampleSchema):
    human_judgment_passed: bool | None = Field(
        ...,
        description=(
            "Whether or not the judgment passed or not.w"
            " If null it means the judgment was not made yet or its a llm only evaluation."
        ),
    )
    llm_judgments_count: int = Field(..., description="Total number of llm judgments")
    llm_judgments_count_completed: int = Field(
        ..., description="Total number of llm completed judgments"
    )
    llm_judgments_count_passed: int = Field(
        ...,
        description=(
            "Number of matching llm judgments against the human judgments if eval type"
            " is human_and_llm, otherwise number of passed llm judgments"
        ),
    )
    llm_judgments_completed: bool = Field(
        ..., description="Whether all LLM judgments are done"
    )
    total_cost: float = Field(..., description="Total cost for the sample")


class SampleSummaryResponse(BaseModel):
    evaluation_type: EvaluationType
    samples: list[SampleSummary]


class SampleJudgements(SampleSchema):
    human_judgment: JudgmentSchema | None
    llm_judgements: list[JudgmentSchema]
