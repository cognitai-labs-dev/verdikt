from src.constants import EvaluationType, JudgmentStatus
from src.schemas.judgment import JudgmentSchema


class JudgementQueries:
    @staticmethod
    def pass_count(
        evaluation_type: EvaluationType,
        llm_judgements: list[JudgmentSchema],
        human: JudgmentSchema | None,
    ) -> int:
        if evaluation_type == EvaluationType.HUMAN_AND_LLM:
            if human is None or human.passed is None:
                return 0

            return sum(
                1
                for llm in llm_judgements
                if llm.passed == human.passed
            )
        else:
            return sum(1 for j in llm_judgements if j.passed)

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
        llm_judgements: list[JudgmentSchema],
    ) -> float:
        total = 0.0
        for judgement in llm_judgements:
            total += judgement.input_tokens_cost or 0
            total += judgement.output_tokens_cost or 0
        return total
