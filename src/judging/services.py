from src.api.v1.schemas import SampleJudgements, SampleSummary
from src.constants import JudgmentStatus, JudgmentType
from src.crud.judgment import judgment_crud
from src.crud.sample import samples_crud
from src.judging.schemas import JudgmentResult, PricingSchema
from src.schemas.judgment import JudgmentSchema, JudgmentUpdateSchema
from src.schemas.sample import SampleSchema


class JudgmentService:
    def __init__(self):
        self.judgment = judgment_crud
        self.sample = samples_crud

    def sample_judgements(self, sample_id: int) -> SampleJudgements | None:
        sample = self.sample.get(sample_id)
        if sample is None:
            return None

        human_judgment = self.judgment.get_human_judgement_by_sample_id(sample_id)
        llm_judgments = self.judgment.get_llm_judgmenets_by_sample_id(sample_id)

        return SampleJudgements(
            **sample.model_dump(),
            human_judgment=human_judgment,
            llm_judgements=llm_judgments,
        )

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
                self.create_llm_only_sample_summary(llm_judgments, sample)
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
                self.create_human_sample_summary(human_judgment, llm_judgments, sample)
            )

        return sample_responses

    @staticmethod
    def create_llm_only_sample_summary(
        llm_judgments: list[JudgmentSchema],
        sample: SampleSchema,
    ) -> SampleSummary:
        completed_judgments = [
            judgement
            for judgement in llm_judgments
            if judgement.status == JudgmentStatus.COMPLETED
        ]

        count_all = len(llm_judgments)

        return SampleSummary(
            **sample.model_dump(),
            human_judgment_passed=None,
            llm_judgments_count=count_all,
            llm_judgments_count_passed=len(
                [judgement for judgement in llm_judgments if judgement.passed]
            ),
            llm_judgments_completed=len(completed_judgments) == count_all,
            llm_judgments_count_completed=len(completed_judgments),
        )

    @staticmethod
    def create_human_sample_summary(
        human_judgment: JudgmentSchema | None,
        llm_judgments: list[JudgmentSchema],
        sample: SampleSchema,
    ) -> SampleSummary:
        completed_judgments = [
            judgement
            for judgement in llm_judgments
            if judgement.status == JudgmentStatus.COMPLETED
        ]

        count_passed = 0
        if human_judgment is not None and human_judgment.passed is not None:
            count_passed = len(
                [
                    judgement
                    for judgement in llm_judgments
                    if judgement.passed == human_judgment.passed
                ]
            )
        count_all = len(llm_judgments)

        return SampleSummary(
            **sample.model_dump(),
            human_judgment_passed=human_judgment.passed if human_judgment else None,
            llm_judgments_count=count_all,
            llm_judgments_count_passed=count_passed,
            llm_judgments_completed=len(completed_judgments) == count_all,
            llm_judgments_count_completed=len(completed_judgments),
        )

    @staticmethod
    def save_judgment(
        judgment_id: int, result: JudgmentResult, pricing: PricingSchema | None = None
    ):
        update_schema = JudgmentUpdateSchema(
            id=judgment_id, status=JudgmentStatus.COMPLETED
        )

        update_schema.reasoning = result.reasoning
        update_schema.passed = result.passed

        if pricing:
            update_schema.input_tokens = pricing.input_tokens
            update_schema.output_tokens = pricing.output_tokens
            update_schema.input_tokens_cost = pricing.output_tokens_cost
            update_schema.output_tokens_cost = pricing.output_tokens_cost

        judgment_crud.update(update_schema)
