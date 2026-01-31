from src.api.v1.schemas import SampleSummary
from src.constants import EvaluationType, JudgmentStatus, JudgmentType
from src.repositories.judgment import judgment_repository
from src.repositories.sample import samples_repository
from src.schemas.judgment import JudgmentSchema
from src.schemas.sample import SampleSchema


class JudgementStatisticsService:
    def __init__(self):
        self.judgment = judgment_repository
        self.sample = samples_repository

    def sample_judgments_summary(
        self, evaluation_id: int, eval_type: EvaluationType
    ) -> list[SampleSummary]:
        samples = self.sample.get_many_by_evaluation(evaluation_id)
        samples_mapped = {s.id: s for s in samples}
        sample_ids = list(samples_mapped.keys())

        llm_judgments_map = self.judgment.get_many_by_sample_ids(
            sample_ids, JudgmentType.LLM
        )
        human_judgments_map = (
            self.judgment.get_human_judgments_by_sample_ids(sample_ids)
            if eval_type == EvaluationType.HUMAN_AND_LLM
            else {}
        )

        sample_responses = []
        for sample_id, sample in samples_mapped.items():
            llm_judgments = llm_judgments_map.get(sample_id, [])
            human_judgment = human_judgments_map.get(sample_id)

            sample_responses.append(
                self._create_sample_summary(sample, human_judgment, llm_judgments)
            )

        return sample_responses

    def _create_sample_summary(
        self,
        sample: SampleSchema,
        human_judgment: JudgmentSchema | None,
        llm_judgments: list[JudgmentSchema],
    ) -> SampleSummary:
        completed, completed_count = self._llm_completion_stats(llm_judgments)

        return SampleSummary(
            **sample.model_dump(),
            human_judgment_passed=human_judgment.passed if human_judgment else None,
            llm_judgments_count=len(llm_judgments),
            llm_judgments_count_passed=self._human_judgement_passed(
                llm_judgments, human_judgment
            ),
            llm_judgments_completed=completed,
            llm_judgments_count_completed=completed_count,
        )

    @staticmethod
    def _human_judgement_passed(
        llm_judgements: list[JudgmentSchema], human: JudgmentSchema | None
    ) -> int:
        if human is not None and human.passed is not None:
            return sum(1 for llm in llm_judgements if llm.passed == human.passed)
        else:
            return sum(1 for j in llm_judgements if j.passed)

    @staticmethod
    def _llm_completion_stats(
        llm_judgments: list[JudgmentSchema],
    ) -> tuple[bool, int]:
        completed_count = sum(
            1 for j in llm_judgments if j.status == JudgmentStatus.COMPLETED
        )
        all_completed = completed_count == len(llm_judgments)
        return all_completed, completed_count
