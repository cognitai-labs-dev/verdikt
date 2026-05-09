from pydantic import BaseModel, Field
from yalc import LLMModel

from src.constants import EvaluationType


class AppAnswerSchema(BaseModel):
    answer: str = Field(
        description="The answer the app produced for the question"
    )
    cost: float | None = Field(
        default=None,
        description="Cost of the app call that produced this answer",
    )


class EvaluationSchema(BaseModel):
    app_id: int
    app_version: str
    app_answers: dict[int, AppAnswerSchema]
    evaluation_type: EvaluationType
    llm_judge_models: list[LLMModel]
