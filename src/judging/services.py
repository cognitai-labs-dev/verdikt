from src.constants import JudgeStatus, JudgeType
from src.crud.judge import judge_crud
from src.judging.schemas import JudgeResult, PricingSchema
from src.schemas.judge import JudgeUpdateSchema


class JudgeService:
    def __init__(self):
        self.crud = judge_crud

    def get_judge_type(self, judge_id: int) -> JudgeType:
        return self.crud.get(judge_id).judge_type

    @staticmethod
    def save_judge(
        judge_id: int, result: JudgeResult, pricing: PricingSchema | None = None
    ):
        update_schema = JudgeUpdateSchema(id=judge_id, status=JudgeStatus.COMPLETED)

        update_schema.score = result.score
        update_schema.reasoning = result.reasoning
        update_schema.passed = result.passed

        if pricing:
            update_schema.input_tokens = pricing.input_tokens
            update_schema.output_tokens = pricing.output_tokens
            update_schema.input_tokens_cost = pricing.output_tokens_cost
            update_schema.output_tokens_cost = pricing.output_tokens_cost

        judge_crud.update(update_schema)
