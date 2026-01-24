from src.constants import JudgeStatus, JudgeType
from src.crud.evaluation import evaluations_crud
from src.crud.judge import judge_crud
from src.judging.schemas import JudgeResult, PricingSchema
from src.schemas.judge import JudgeUpdateSchema, JudgeSchema


class JudgeService:
    def __init__(self):
        self.judge = judge_crud
        self.evaluation = evaluations_crud

    def get_human_judges_by_run_id(self, eval_run_id: int) -> list[JudgeSchema]:
        return self.judge.get_many_by_eval_run(eval_run_id, JudgeType.HUMAN)

    def get_human_judge_by_eval(self, eval_id: int) -> int | None:
        res = self.judge.get_many_by_eval_id(eval_id, JudgeType.HUMAN)
        if res is None:
            return None

        return res.id

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
