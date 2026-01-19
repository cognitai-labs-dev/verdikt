from src.constants import JudgeType
from src.juding.base import BaseJudgeService, JudgeResult


class HumanJudge(BaseJudgeService):
    def __init__(self):
        super().__init__(JudgeType.HUMAN, "Human")

    def _get_judge(self, question: str, answer: str) -> JudgeResult:
        """
        TODO: create interface for interactions so it can be used for web, slack cli ...
        """
        print("question:", question)
        print("answer:", answer)
        text_answer = input("text answer: ")
        final_verdict = input("final verdict (pass/fail): ")
        score = int(input("score (0-100): "))

        return JudgeResult(
            reasoning=text_answer,
            passed=final_verdict == "pass",
            score=score,
        )
