from src.constants import EvaluationType, JudgmentStatus
from src.schemas.judgment import JudgmentSchema


class JudgmentQueries:
    @staticmethod
    def pass_count(
        evaluation_type: EvaluationType,
        llm_judgments: list[JudgmentSchema],
        human: JudgmentSchema | None,
    ) -> int:
        if evaluation_type == EvaluationType.HUMAN_AND_LLM:
            if human is None or human.passed is None:
                return 0

            return sum(
                1
                for llm in llm_judgments
                if llm.passed == human.passed
            )
        else:
            return sum(1 for j in llm_judgments if j.passed)

    @staticmethod
    def llm_completion_count(
        llm_judgments: list[JudgmentSchema],
    ) -> int:
        completed_count = sum(
            1
            for j in llm_judgments
            if j.status == JudgmentStatus.COMPLETED
        )
        return completed_count

    @staticmethod
    def llm_cost(
        llm_judgments: list[JudgmentSchema],
    ) -> float:
        total = 0.0
        for judgment in llm_judgments:
            total += judgment.input_tokens_cost or 0
            total += judgment.output_tokens_cost or 0
        return total
