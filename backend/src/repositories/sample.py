from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncConnection

from src.constants import JudgmentType
from src.db.tables.evaluations import evaluations_table
from src.db.tables.judgments import judgments_table
from src.db.tables.samples import samples_table
from src.repositories.base import BaseRepository
from src.schemas.base import UpdateSchema
from src.schemas.sample import (
    SampleCreateSchema,
    SampleSchema,
    SampleWithJudgmentSchema,
)


class SamplesRepository(
    BaseRepository[SampleCreateSchema, SampleSchema, UpdateSchema]
):
    """Data access layer for samples operations."""

    def __init__(self):
        super().__init__(samples_table, SampleSchema)

    async def get_many_by_evaluation(
        self, conn: AsyncConnection, evaluation_ids: list[int]
    ) -> list[SampleSchema]:
        """Get all samples for a given evaluation ID."""
        stmt = (
            select(samples_table)
            .where(samples_table.c.evaluation_id.in_(evaluation_ids))
            .order_by(samples_table.c.created_at.desc())
        )

        result = await conn.execute(stmt)
        rows = result.fetchall()

        if len(rows) == 0:
            return []
        return [
            SampleSchema.model_validate(row._mapping) for row in rows
        ]

    async def get_many_by_evaluation_with_judgements(
        self,
        conn: AsyncConnection,
        evaluation_id: int,
        judgement_type: JudgmentType,
    ) -> list[SampleWithJudgmentSchema]:
        """Get all samples with judgments for an evaluation.

        Returns flat rows with all sample and judgment
        data, no evaluation data.
        """
        stmt = (
            select(
                samples_table,
                judgments_table.c.id.label("judgment_id"),
                judgments_table.c.created_at.label(
                    "judgment_created_at"
                ),
                judgments_table.c.updated_at.label(
                    "judgment_updated_at"
                ),
                judgments_table.c.sample_id,
                judgments_table.c.status,
                judgments_table.c.judgment_type,
                judgments_table.c.judgment_model,
                judgments_table.c.reasoning,
                judgments_table.c.passed,
                judgments_table.c.input_tokens,
                judgments_table.c.output_tokens,
                judgments_table.c.input_tokens_cost,
                judgments_table.c.output_tokens_cost,
            )
            .join(
                evaluations_table,
                evaluations_table.c.id == self.table.c.evaluation_id,
            )
            .join(
                judgments_table,
                judgments_table.c.sample_id == self.table.c.id,
            )
            .where(
                and_(
                    evaluations_table.c.id == evaluation_id,
                    judgments_table.c.judgment_type == judgement_type,
                )
            )
            .order_by(samples_table.c.created_at.desc())
        )

        result = await conn.execute(stmt)
        rows = result.fetchall()

        if len(rows) == 0:
            return []
        return [
            SampleWithJudgmentSchema.model_validate(row._mapping)
            for row in rows
        ]
