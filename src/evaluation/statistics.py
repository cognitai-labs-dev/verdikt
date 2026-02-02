from collections import defaultdict

from src.api.v1.schemas import (
    EvaluationSummary,
    SampleSummary,
    SummaryResponse,
)
from src.constants import EvaluationType
from src.judgement.statistics import (
    JudgementStatisticsService,
)
from src.repositories.judgment import judgment_repository
from src.repositories.sample import samples_repository
from src.schemas.evaluation import EvaluationSchema


class EvaluationStatisticsService:
    """
    Possible can be reafctored to have 1 base stats class isntead of DI
    Rename services to writers
    Statitics to queries

    """

    def __init__(self, service: JudgementStatisticsService):
        self.judgment = judgment_repository
        self.sample = samples_repository
        self.judge_stats_service = service

    def evaluation_summaries_by_eval_ids(
        self,
        evaluations: list[EvaluationSchema],
        evaluation_type: EvaluationType,
    ) -> list[EvaluationSummary]:
        evaluations_mapped = {
            evaluation.id: evaluation for evaluation in evaluations
        }
        samples_summaries = (
            self.judge_stats_service.samples_summary_by_eval_ids(
                list(evaluations_mapped.keys()), evaluation_type
            )
        )
        sample_summaries_mapped = self._group_sample_summaries(
            samples_summaries
        )

        evaluation_summaries = []

        for (
            eval_id,
            summaries,
        ) in sample_summaries_mapped.items():
            evaluation = evaluations_mapped[eval_id]
            aggregated = SummaryResponse.from_summaries(summaries)

            humans = 0
            humans_completed = 0
            if evaluation_type == EvaluationType.HUMAN_AND_LLM:
                humans = len(summaries)
                humans_completed = sum(
                    [
                        1
                        for summary in summaries
                        if summary.human_judgment_passed is not None
                    ]
                )

            evaluation_summaries.append(
                EvaluationSummary(
                    **evaluation.model_dump(),
                    **aggregated.model_dump(),
                    human_judgement_count=humans,
                    human_judgement_count_completed=humans_completed,
                ),
            )

        return evaluation_summaries

    @staticmethod
    def _group_sample_summaries(
        summaries: list[SampleSummary],
    ) -> dict[int, list[SampleSummary]]:
        result = defaultdict(list)

        for summary in summaries:
            result[summary.evaluation_id].append(summary)
        return dict(result)
