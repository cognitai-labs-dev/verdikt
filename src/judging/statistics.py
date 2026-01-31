from src.api.v1.schemas import SampleSummary
from src.constants import JudgmentStatus, JudgmentType
from src.repositories.judgment import judgment_repository
from src.repositories.sample import samples_repository
from src.schemas.judgment import JudgmentSchema
from src.schemas.sample import SampleSchema


class JudgementStatisticsService:
    def __init__(self):
        self.judgment = judgment_repository
        self.sample = samples_repository

    def sample_judgments_summary_llm_only(
        self, evaluation_id: int
    ) -> list[SampleSummary]:
        samples = self.sample.get_many_by_evaluation(evaluation_id)
        sample_ids = {s.id: s for s in samples}
        llm_judgments_map = self.judgment.get_many_by_sample_ids(
            list(sample_ids.keys()), JudgmentType.LLM
        )

        sample_responses = []
        for sample_id, sample in sample_ids.items():
            llm_judgments = llm_judgments_map.get(sample_id, [])

            sample_responses.append(
                self._create_llm_only_sample_summary(llm_judgments, sample)
            )

        return sample_responses

    def sample_judgments_summary_human(self, evaluation_id: int) -> list[SampleSummary]:
        samples = self.sample.get_many_by_evaluation(evaluation_id)
        sample_ids = {s.id: s for s in samples}
        human_judgments_map = self.judgment.get_human_judgments_by_sample_ids(
            list(sample_ids.keys())
        )
        llm_judgments_map = self.judgment.get_many_by_sample_ids(
            list(sample_ids.keys()), JudgmentType.LLM
        )

        sample_responses = []
        for sample_id, sample in sample_ids.items():
            human_judgment = human_judgments_map.get(sample_id)
            llm_judgments = llm_judgments_map.get(sample_id, [])

            sample_responses.append(
                self._create_human_sample_summary(human_judgment, llm_judgments, sample)
            )

        return sample_responses

    def _create_llm_only_sample_summary(
        self,
        llm_judgments: list[JudgmentSchema],
        sample: SampleSchema,
    ) -> SampleSummary:
        completed, completed_count = self._llm_completion_stats(llm_judgments)

        return SampleSummary(
            **sample.model_dump(),
            human_judgment_passed=None,
            llm_judgments_count=len(llm_judgments),
            llm_judgments_count_passed=len(
                [judgement for judgement in llm_judgments if judgement.passed]
            ),
            llm_judgments_completed=completed,
            llm_judgments_count_completed=completed_count,
        )

    def _create_human_sample_summary(
        self,
        human_judgment: JudgmentSchema | None,
        llm_judgments: list[JudgmentSchema],
        sample: SampleSchema,
    ) -> SampleSummary:
        completed, completed_count = self._llm_completion_stats(llm_judgments)

        count_passed = 0
        if human_judgment is not None and human_judgment.passed is not None:
            count_passed = len(
                [
                    judgement
                    for judgement in llm_judgments
                    if judgement.passed == human_judgment.passed
                ]
            )

        return SampleSummary(
            **sample.model_dump(),
            human_judgment_passed=human_judgment.passed if human_judgment else None,
            llm_judgments_count=len(llm_judgments),
            llm_judgments_count_passed=count_passed,
            llm_judgments_completed=completed,
            llm_judgments_count_completed=completed_count,
        )

    @staticmethod
    def _llm_completion_stats(
        llm_judgments: list[JudgmentSchema],
    ) -> tuple[bool, int]:
        completed_count = sum(
            1 for j in llm_judgments if j.status == JudgmentStatus.COMPLETED
        )
        all_completed = completed_count == len(llm_judgments)
        return all_completed, completed_count
