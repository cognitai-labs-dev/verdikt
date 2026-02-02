from src.constants import JudgmentStatus
from src.judgement.schemas import JudgmentResult, PricingSchema
from src.repositories.judgment import judgment_repository
from src.repositories.sample import samples_repository
from src.schemas.judgment import JudgmentUpdateSchema


class JudgmentService:
    def __init__(self):
        self.judgment = judgment_repository
        self.sample = samples_repository

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
