from pydantic import BaseModel, Field

from src.constants import EvaluationType
from src.schemas.judgment import JudgmentSchema
from src.schemas.sample import SampleSchema


class JudgmentRequest(BaseModel):
    reasoning: str
    passed: bool


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


class SampleSummaryResponse(BaseModel):
    evaluation_type: EvaluationType
    samples: list[SampleSummary]


class SampleJudgements(SampleSchema):
    human_judgment: JudgmentSchema | None
    llm_judgements: list[JudgmentSchema]
