"""
Schemas for API responses & requests
"""

from pydantic import BaseModel, Field
from yalc import LLMModel

from src.constants import EvaluationType
from src.schemas.evaluation import EvaluationSchema
from src.schemas.judgment import JudgmentSchema
from src.schemas.sample import SampleSchema


class EvaluationRequest(BaseModel):
    app_version: str
    evaluation_type: EvaluationType
    app_answers: dict[int, str] = Field(
        description="a dict of values where the key is the dataset id and the value is the app answer to the question"
    )
    llm_judge_models: list[LLMModel] = list(LLMModel)


class AppRequest(BaseModel):
    name: str


class AppDatasetItem(BaseModel):
    question: str
    human_answer: str


class AppDatasetsRequest(BaseModel):
    datasets: list[AppDatasetItem]


class JudgmentRequest(BaseModel):
    reasoning: str
    passed: bool


class SummaryResponse(BaseModel):
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

    @classmethod
    def empty(cls) -> "SummaryResponse":
        return cls(
            llm_judgments_count=0,
            llm_judgments_count_completed=0,
            llm_judgments_count_passed=0,
            total_cost=0.0,
        )

    @classmethod
    def from_summaries(
        cls, summaries: list["SampleSummary"]
    ) -> "SummaryResponse":
        res = cls.empty()
        for summary in summaries:
            res.llm_judgments_count += summary.llm_judgments_count
            res.llm_judgments_count_passed += (
                summary.llm_judgments_count_passed
            )
            res.llm_judgments_count_completed += (
                summary.llm_judgments_count_completed
            )
            res.total_cost += summary.total_cost

        return res


class EvaluationSummary(SummaryResponse, EvaluationSchema):
    human_judgement_count: int
    human_judgement_count_completed: int


class SampleSummary(SummaryResponse, SampleSchema):
    evaluation_type: EvaluationType
    human_judgment_passed: bool | None = Field(
        ...,
        description=(
            "Whether or not the judgment passed or not."
            " If null it means the judgment was not made yet or its a llm only evaluation."
        ),
    )


class SampleJudgements(SampleSummary):
    human_judgment: JudgmentSchema | None
    llm_judgements: list[JudgmentSchema]
