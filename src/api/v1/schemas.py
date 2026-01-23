from pydantic import BaseModel


class HumanJudgeRequest(BaseModel):
    reasoning: str
    passed: bool
    score: int
