from src.constants import JudgmentStatus, JudgmentType
from src.crud.sample import samples_crud
from src.crud.judgment import judgment_crud
from src.judging.schemas import JudgmentResult, PricingSchema
from src.api.v1.schemas import HumanSampleSummary, SampleDetail
from src.schemas.judgment import JudgmentUpdateSchema, JudgmentSchema
from src.schemas.sample import SampleSchema


class JudgmentService:
    def __init__(self):
        self.judgment = judgment_crud
        self.sample = samples_crud

    def sample_judgment_detail(self, sample_id: int) -> SampleDetail:
        sample = self.sample.get(sample_id)
        human_judgments = self.judgment.get_many_by_sample_ids(
            [sample_id], JudgmentType.HUMAN
        ).get(sample_id)
        llm_judgments = self.judgment.get_many_by_sample_ids(
            [sample_id], JudgmentType.LLM
        ).get(sample_id)

        return SampleDetail(
            **sample.model_dump(),
            human_judgment=self._get_human_judgment(human_judgments),
            llm_judgements=llm_judgments,
        )

    def sample_judgments_summary_human(self, evaluation_id: int) -> list[HumanSampleSummary]:
        samples = self.sample.get_many_by_evaluation(evaluation_id)
        sample_ids = {s.id: s for s in samples}
        human_judgments_map = self.judgment.get_many_by_sample_ids(
            list(sample_ids.keys()), JudgmentType.HUMAN
        )
        llm_judgments_map = self.judgment.get_many_by_sample_ids(
            list(sample_ids.keys()), JudgmentType.LLM
        )

        sample_responses = []
        for sample_id, sample in sample_ids.items():
            human_judgment = self._get_human_judgment(
                human_judgments_map.get(sample_id)
            )
            llm_judgments = llm_judgments_map.get(sample_id)

            self.create_human_sample_summary(human_judgment, llm_judgments, sample)

        return sample_responses

    @staticmethod
    def create_human_sample_summary(
        human_judgment: JudgmentSchema | None,
        llm_judgments: list[JudgmentSchema],
        sample: SampleSchema,
    ) -> HumanSampleSummary:
        return HumanSampleSummary(
            **sample.model_dump(),
            human_judgment_passed=human_judgment.passed if human_judgment else None,
            llm_judgments_count=len(llm_judgments),
            llm_judgments_count_matching=len(
                [
                    judgement
                    for judgement in llm_judgments
                    if judgement.passed == human_judgment.passed
                ]
            ),
        )

    def get_human_judgment_by_sample(self, sample_id: int) -> JudgmentSchema | None:
        results = self.judgment.get_many_by_sample_id(sample_id, JudgmentType.HUMAN)
        if len(results) == 0:
            return None
        if len(results) > 1:
            raise RuntimeError("More than 1 human judgment for a sample")

        return results[0]

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

    @staticmethod
    def _get_human_judgment(
        human_judgements: list[JudgmentSchema],
    ) -> JudgmentSchema | None:
        if len(human_judgements) == 1:
            return human_judgements[0]
        elif len(human_judgements) == 0:
            return None

        raise RuntimeError("More than 1 human judgment for a sample")
