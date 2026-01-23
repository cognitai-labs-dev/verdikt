from pydantic import BaseModel


class HumanJudgeRequest(BaseModel):
    judge_id: int
    reasoning: str
    passed: bool
    score: int
