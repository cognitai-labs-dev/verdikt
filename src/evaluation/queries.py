from collections import defaultdict

from src.api.v1.schemas import (
    EvaluationSummary,
    SampleSummary,
    SummaryResponse,
)
from src.constants import EvaluationType
from src.repositories.judgment import judgment_repository
from src.repositories.sample import samples_repository
from src.sample.queries import SampleQueries
from src.schemas.evaluation import EvaluationSchema


class EvaluationQueries:
    """
    Possible can be reafctored to have 1 base stats class isntead of DI
    Rename services to command
    Statitics to queries

    Use  Composition Root pattern

    """

    def __init__(self):
        self.judgment = judgment_repository
        self.sample = samples_repository
        self.sample_queries = SampleQueries()

    def evaluation_summaries_by_eval_ids(
        self,
        evaluations: list[EvaluationSchema],
        evaluation_type: EvaluationType,
    ) -> list[EvaluationSummary]:
        evaluations_mapped = {
            evaluation.id: evaluation for evaluation in evaluations
        }
        samples_summaries = self.sample_queries.summary_by_eval_ids(
            list(evaluations_mapped.keys()), evaluation_type
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
            humans_count, humans_completed = (
                self.sample_queries.human_passed_count(
                    evaluation_type, summaries
                )
            )

            evaluation_summaries.append(
                EvaluationSummary(
                    **evaluation.model_dump(),
                    **aggregated.model_dump(),
                    human_judgement_count=humans_count,
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
