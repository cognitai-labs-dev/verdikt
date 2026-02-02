from src.api.v1.schemas import SampleJudgements, SampleSummary
from src.constants import (
    EvaluationType,
    JudgmentType,
)
from src.repositories.evaluation import evaluations_repository
from src.repositories.judgment import judgment_repository
from src.repositories.sample import samples_repository
from src.sample.service import SampleService
from src.schemas.sample import SampleSchema


class JudgementStatisticsService:
    def __init__(self):
        self.judgment = judgment_repository
        self.sample = samples_repository
        self.evaluation = evaluations_repository
        self.sample_service = SampleService()

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
                self.sample_service.sample_summary(
                    eval_type, sample, human_judgment, llm_judgments
                )
            )

        return sample_responses
