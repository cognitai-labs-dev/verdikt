from pydantic import BaseModel


class EvaluationRequest(BaseModel):
    reasoning: str
    passed: bool
    score: int
