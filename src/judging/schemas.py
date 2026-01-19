from typing import NamedTuple

from pydantic import BaseModel


class LLMJudgeConfig(NamedTuple):
    provider: str
    model: str


class JudgeResult(BaseModel):
    reasoning: str
    passed: bool
    score: int
