import logging
from abc import ABC, abstractmethod

from pydantic import BaseModel

from src.constants import JudgeType


class JudgeResult(BaseModel):
    reasoning: str
    passed: bool
    score: int


class BaseJudgeService(ABC):
    def __init__(self, judge_type: JudgeType, judge_model: str):
        self.type = judge_type
        self.model = judge_model
        self.logger = logging.getLogger(__name__)

    def judge(self, question: str, answer: str) -> JudgeResult:
        self.logger.info("Running %s judge", self.type)
        return self._get_judge_result(question, answer)

    @abstractmethod
    def _get_judge_result(self, question: str, answer: str) -> JudgeResult:
        """
        Implement either for human or llm
        """
        pass
