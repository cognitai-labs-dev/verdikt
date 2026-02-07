from pydantic import BaseModel

from src.constants import EvaluationType


class EvaluationSchema(BaseModel):
    app_id: int
    app_version: str
    app_answers: dict[int, str]
    evaluation_type: EvaluationType
