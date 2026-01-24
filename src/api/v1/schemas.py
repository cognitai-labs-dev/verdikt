from pydantic import BaseModel


class JudgmentRequest(BaseModel):
    reasoning: str
    passed: bool
    score: int
