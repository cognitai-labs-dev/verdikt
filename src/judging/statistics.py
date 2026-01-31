from src.api.v1.schemas import SampleJudgements, SampleSummary
from src.constants import (
    EvaluationType,
    JudgmentStatus,
    JudgmentType,
)
from src.repositories.evaluation import evaluations_repository
from src.repositories.judgment import judgment_repository
from src.repositories.sample import samples_repository
from src.schemas.judgment import JudgmentSchema
from src.schemas.sample import SampleSchema


class JudgementStatisticsService:
    def __init__(self):
        self.judgment = judgment_repository
        self.sample = samples_repository
        self.evaluation = evaluations_repository

    def samples_summary_by_eval_ids(
        self,
        evaluation_ids: list[int],
        eval_type: EvaluationType,
    ) -> list[SampleSummary]:
        samples = self.sample.get_many_by_evaluation(evaluation_ids)
        return self._samples_summary(samples, eval_type)

    def samples_summary_by_sample_ids(
        self,
        sample_ids: list[int],
        eval_type: EvaluationType,
    ) -> list[SampleSummary]:
        samples = self.sample.get_by_many_ids(sample_ids)
        return self._samples_summary(samples, eval_type)

    def sample_judgements_with_summary(
        self, sample_id: int
    ) -> SampleJudgements | None:
        sample = self.sample.get(sample_id)
        if sample is None:
            return None

        evaluation = self.evaluation.get(sample.evaluation_id)
        if evaluation is None:
            return None

        summary = self._samples_summary([sample], evaluation.type)
        if len(summary) == 0:
            return None

        human_judgment = (
            self.judgment.get_human_judgement_by_sample_id(sample_id)
        )
        llm_judgments = self.judgment.get_llm_judgmenets_by_sample_id(
            sample_id
        )

        return SampleJudgements(
            **summary[0].model_dump(),
            human_judgment=human_judgment,
            llm_judgements=llm_judgments,
        )

    def _samples_summary(
        self,
        samples: list[SampleSchema],
        eval_type: EvaluationType,
    ) -> list[SampleSummary]:
        """
        Core method for calculating statistics for sample/judgement pairs
        This will get called multiple times for the same sample, for perf
        optimalization add caching by sample_id -> sample_summary
        """
        if len(samples) == 0:
            return []

        samples_mapped = {sample.id: sample for sample in samples}
        sample_ids = list(samples_mapped.keys())

        llm_judgments_map = self.judgment.get_many_by_sample_ids(
            sample_ids, JudgmentType.LLM
        )
        human_judgments_map = (
            self.judgment.get_human_judgments_by_sample_ids(
                sample_ids
            )
            if eval_type == EvaluationType.HUMAN_AND_LLM
            else {}
        )

        sample_responses = []
        for sample_id, sample in samples_mapped.items():
            llm_judgments = llm_judgments_map.get(sample_id, [])
            human_judgment = human_judgments_map.get(sample_id)

            sample_responses.append(
                self._create_sample_summary(
                    eval_type, sample, human_judgment, llm_judgments
                )
            )

        return sample_responses

    def _create_sample_summary(
        self,
        evaluation_type: EvaluationType,
        sample: SampleSchema,
        human_judgment: JudgmentSchema | None,
        llm_judgments: list[JudgmentSchema],
    ) -> SampleSummary:
        completed_count = self._llm_completion_stats(llm_judgments)

        return SampleSummary(
            **sample.model_dump(),
            evaluation_type=evaluation_type,
            human_judgment_passed=human_judgment.passed
            if human_judgment
            else None,
            llm_judgments_count=len(llm_judgments),
            llm_judgments_count_passed=self._judgement_passed(
                evaluation_type, llm_judgments, human_judgment
            ),
            llm_judgments_count_completed=completed_count,
            total_cost=self._get_total_cost(llm_judgments)
            + (sample.app_cost or 0),
        )

    @staticmethod
    def _judgement_passed(
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
