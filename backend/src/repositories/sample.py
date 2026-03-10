from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncConnection

from src.constants import JudgmentType
from src.db.tables.judgments import judgments_table
from src.db.tables.samples import samples_table
from src.repositories.base import BaseRepository
from src.schemas.base import UpdateSchema
from src.schemas.sample import (
    SampleCreateSchema,
    SampleJudgmentSummarySchema,
    SampleSchema,
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

    async def get_many_by_evaluation_with_judgments(
        self,
        conn: AsyncConnection,
        evaluation_id: int,
        judgment_type: JudgmentType,
    ) -> list[SampleJudgmentSummarySchema]:
        """Get lightweight judgment summaries for an evaluation.

        Returns only sample_id, status, and passed for
        building navigation lists.
        """
        stmt = (
            select(
                judgments_table.c.sample_id,
                judgments_table.c.status,
                judgments_table.c.passed,
            )
            .join(
                samples_table,
                samples_table.c.id == judgments_table.c.sample_id,
            )
            .where(
                and_(
                    samples_table.c.evaluation_id == evaluation_id,
                    judgments_table.c.judgment_type == judgment_type,
                )
            )
            .order_by(samples_table.c.created_at.desc())
        )

        result = await conn.execute(stmt)
        rows = result.fetchall()

        if len(rows) == 0:
            return []
        return [
            SampleJudgmentSummarySchema.model_validate(row._mapping)
            for row in rows
        ]
