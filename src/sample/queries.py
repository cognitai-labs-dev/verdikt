from src.api.v1.schemas import SampleJudgements, SampleSummary
from src.constants import (
    EvaluationType,
    JudgmentType,
)
from src.judgement.queries import JudgementQueries
from src.repositories.evaluation import evaluations_repository
from src.repositories.judgment import judgment_repository
from src.repositories.sample import samples_repository
from src.schemas.judgment import JudgmentSchema
from src.schemas.sample import SampleSchema


class SampleQueries:
    def __init__(self):
        self.judgment = judgment_repository
        self.sample = samples_repository
        self.evaluation = evaluations_repository
        self.judgement_queries = JudgementQueries()

    def summary(
        self,
        samples: list[SampleSchema],
        evaluation_type: EvaluationType,
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
            if evaluation_type == EvaluationType.HUMAN_AND_LLM
            else {}
        )

        sample_responses = []
        for sample_id, sample in samples_mapped.items():
            llm_judgments = llm_judgments_map.get(sample_id, [])
            human_judgment = human_judgments_map.get(sample_id)

            sample_responses.append(
                self._sample_summary(
                    sample,
                    llm_judgments,
                    human_judgment,
                    evaluation_type,
                )
            )

        return sample_responses

    def summary_by_eval_ids(
        self,
        evaluation_ids: list[int],
        eval_type: EvaluationType,
    ) -> list[SampleSummary]:
        samples = self.sample.get_many_by_evaluation(evaluation_ids)
        return self.summary(samples, eval_type)

    def summary_by_sample_ids(
        self,
        sample_ids: list[int],
        eval_type: EvaluationType,
    ) -> list[SampleSummary]:
        samples = self.sample.get_by_many_ids(sample_ids)
        return self.summary(samples, eval_type)

    def judgements_with_summary(
        self, sample_id: int
    ) -> SampleJudgements | None:
        sample = self.sample.get(sample_id)
        if sample is None:
            return None

        evaluation = self.evaluation.get(sample.evaluation_id)
        if evaluation is None:
            return None

        summary = self.summary([sample], evaluation.type)
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

    def human_passed_count(
        self,
        evaluation_type: EvaluationType,
        summaries: list[SampleSummary],
    ) -> tuple[int, int]:
        human_judgements_count = 0
        human_judgements_completed = 0
        if evaluation_type == EvaluationType.HUMAN_AND_LLM:
            human_judgements_count = len(summaries)
            human_judgements_completed = sum(
                [
                    1
                    for summary in summaries
                    if summary.human_judgment_passed is not None
                ]
            )

        return human_judgements_count, human_judgements_completed

    def _sample_summary(
        self,
        sample: SampleSchema,
        llm_judgments: list[JudgmentSchema],
        human_judgment: JudgmentSchema | None,
        evaluation_type: EvaluationType,
    ) -> SampleSummary:
        """
        Create a sample summary from the judgements
        """
        total_cost = self.judgement_queries.llm_cost(
            llm_judgments
        ) + (sample.app_cost or 0)
        human_passed = (
            human_judgment.passed if human_judgment else None
        )

        return SampleSummary(
            **sample.model_dump(),
            evaluation_type=evaluation_type,
            human_judgment_passed=human_passed,
            llm_judgments_count=len(llm_judgments),
            llm_judgments_count_passed=self.judgement_queries.pass_count(
                evaluation_type, llm_judgments, human_judgment
            ),
            llm_judgments_count_completed=self.judgement_queries.llm_completion_count(
                llm_judgments
            ),
            total_cost=total_cost,
        )
