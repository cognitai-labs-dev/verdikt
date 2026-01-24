from src.constants import JudgmentStatus, JudgmentType
from src.crud.sample import samples_crud
from src.crud.judgment import judgment_crud
from src.judging.schemas import JudgmentResult, PricingSchema
from src.schemas.judgment import JudgmentUpdateSchema


class JudgmentService:
    def __init__(self):
        self.judgment = judgment_crud
        self.sample = samples_crud

    def get_human_judgment_by_sample(self, sample_id: int) -> int | None:
        results = self.judgment.get_many_by_sample_id(sample_id, JudgmentType.HUMAN)
        if len(results) == 0:
            return None
        if len(results) > 1:
            raise RuntimeError("More than 1 human judgment for a sample")

        return results[0].id

    @staticmethod
    def save_judgment(
        judgment_id: int, result: JudgmentResult, pricing: PricingSchema | None = None
    ):
        update_schema = JudgmentUpdateSchema(
            id=judgment_id, status=JudgmentStatus.COMPLETED
        )

        update_schema.score = result.score
        update_schema.reasoning = result.reasoning
        update_schema.passed = result.passed

        if pricing:
            update_schema.input_tokens = pricing.input_tokens
            update_schema.output_tokens = pricing.output_tokens
            update_schema.input_tokens_cost = pricing.output_tokens_cost
            update_schema.output_tokens_cost = pricing.output_tokens_cost

        judgment_crud.update(update_schema)
