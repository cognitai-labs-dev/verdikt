from src.api.v1.schemas import SampleJudgements
from src.constants import JudgmentStatus
from src.judging.schemas import JudgmentResult, PricingSchema
from src.repositories.judgment import judgment_repository
from src.repositories.sample import samples_repository
from src.schemas.judgment import JudgmentUpdateSchema


class JudgmentService:
    def __init__(self):
        self.judgment = judgment_repository
        self.sample = samples_repository

    def sample_judgements(
        self, sample_id: int
    ) -> SampleJudgements | None:
        sample = self.sample.get(sample_id)
        if sample is None:
            return None

        human_judgment = (
            self.judgment.get_human_judgement_by_sample_id(sample_id)
        )
        llm_judgments = self.judgment.get_llm_judgmenets_by_sample_id(
            sample_id
        )

        return SampleJudgements(
            **sample.model_dump(),
            human_judgment=human_judgment,
            llm_judgements=llm_judgments,
        )

    @staticmethod
    def save_judgment(
        judgment_id: int,
        result: JudgmentResult,
        pricing: PricingSchema | None = None,
    ):
        update_schema = JudgmentUpdateSchema(
            id=judgment_id, status=JudgmentStatus.COMPLETED
        )

        update_schema.reasoning = result.reasoning
        update_schema.passed = result.passed

        if pricing:
            update_schema.input_tokens = pricing.input_tokens
            update_schema.output_tokens = pricing.output_tokens
            update_schema.input_tokens_cost = (
                pricing.output_tokens_cost
            )
            update_schema.output_tokens_cost = (
                pricing.output_tokens_cost
            )

        judgment_repository.update(update_schema)
