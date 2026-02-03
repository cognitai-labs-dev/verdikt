from src.api.v1.schemas import SampleSummary
from src.constants import (
    EvaluationType,
    JudgmentStatus,
)
from src.schemas.judgment import JudgmentSchema
from src.schemas.sample import SampleSchema


class SampleQueries:
    def sample_summary(
        self,
        evaluation_type: EvaluationType,
        sample: SampleSchema,
        human_judgment: JudgmentSchema | None,
        llm_judgments: list[JudgmentSchema],
    ) -> SampleSummary:
        return SampleSummary(
            **sample.model_dump(),
            evaluation_type=evaluation_type,
            human_judgment_passed=human_judgment.passed
            if human_judgment
            else None,
            llm_judgments_count=len(llm_judgments),
            llm_judgments_count_passed=self._judgement_stats(
                evaluation_type, llm_judgments, human_judgment
            ),
            llm_judgments_count_completed=self._llm_completion_stats(
                llm_judgments
            ),
            total_cost=self._get_total_cost(llm_judgments)
            + (sample.app_cost or 0),
        )

    @staticmethod
    def _judgement_stats(
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
    def _llm_completion_stats(
        llm_judgments: list[JudgmentSchema],
    ) -> int:
        completed_count = sum(
            1
            for j in llm_judgments
            if j.status == JudgmentStatus.COMPLETED
        )
        return completed_count

    @staticmethod
    def _get_total_cost(
        llm_judgements: list[JudgmentSchema],
    ) -> float:
        total = 0.0
        for judgement in llm_judgements:
            total += judgement.input_tokens_cost or 0
            total += judgement.output_tokens_cost or 0
        return total
