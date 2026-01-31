from pydantic import BaseModel, Field

from src.constants import EvaluationType
from src.schemas.evaluation import EvaluationSchema
from src.schemas.judgment import JudgmentSchema
from src.schemas.sample import SampleSchema


class JudgmentRequest(BaseModel):
    reasoning: str
    passed: bool


class SummarySchema(BaseModel):
    llm_judgments_count: int = Field(
        description="Total number of llm judgments"
    )
    llm_judgments_count_passed: int = Field(
        description=(
            "Number of matching llm judgments against the human judgments if eval type is human_and_llm, otherwise number of passed llm judgments"
        ),
    )
    llm_judgments_count_completed: int = Field(
        description="Total number of llm completed judgments",
    )
    total_cost: float = Field(description="Total cost for the sample")


class EvaluationSummary(SummarySchema, EvaluationSchema):
    human_judgement_count: int
    human_judgement_count_completed: int


class SampleSummary(SummarySchema, SampleSchema):
    human_judgment_passed: bool | None = Field(
        ...,
        description=(
            "Whether or not the judgment passed or not."
            " If null it means the judgment was not made yet or its a llm only evaluation."
        ),
    )


class SampleSummaryResponse(BaseModel):
    evaluation_type: EvaluationType
    samples: list[SampleSummary]


class SampleJudgements(SampleSchema):
    human_judgment: JudgmentSchema | None
    llm_judgements: list[JudgmentSchema]
