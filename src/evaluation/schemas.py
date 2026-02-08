from pydantic import BaseModel
from yalc import LLMModel

from src.constants import EvaluationType


class EvaluationSchema(BaseModel):
    app_id: int
    app_version: str
    app_answers: dict[int, str]
    evaluation_type: EvaluationType
    llm_judge_models: list[LLMModel]
