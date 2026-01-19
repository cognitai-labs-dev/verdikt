import logging
from abc import ABC, abstractmethod

from pydantic import BaseModel

from src.constants import JudgeType
from src.crud.judge_result import judge_results_crud


class JudgeResult(BaseModel):
    reasoning: str
    passed: bool
    score: int


class BaseJudgeService(ABC):
    def __init__(self, judge_type: JudgeType, judge_model: str):
        self.crud = judge_results_crud
        self.type = judge_type
        self.model = judge_model
        self.logger = logging.getLogger(__name__)

    def start(self, judge_result_id: int) -> None:
        self.logger.info("Running %s judge", self.type)
        # return self._get_judge_result(judge_result., answer)

    @abstractmethod
    def _get_judge_result(self, question: str, answer: str) -> JudgeResult:
        """
        Implement either for human or llm
        """
        pass
