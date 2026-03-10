from sqlalchemy.ext.asyncio import AsyncConnection

from src.constants import JudgmentStatus
from src.judgment.schemas import JudgmentResult, PricingSchema
from src.repositories.judgment import JudgmentRepository
from src.schemas.judgment import JudgmentUpdateSchema


class JudgmentCommands:
    def __init__(self, judgment_repo: JudgmentRepository):
        self.judgment = judgment_repo

    async def create(
        self,
        conn: AsyncConnection,
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

        await self.judgment.update(conn, update_schema)
