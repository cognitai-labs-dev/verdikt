from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncConnection

from src.constants import EvaluationType
from src.db.tables.evaluations import evaluations_table
from src.repositories.base import BaseRepository
from src.schemas.base import UpdateSchema
from src.schemas.evaluation import (
    EvaluationCreateSchema,
    EvaluationSchema,
)


class EvaluationsRepository(
    BaseRepository[
        EvaluationCreateSchema, EvaluationSchema, UpdateSchema
    ]
):
    """Data access layer for evaluations operations."""

    def __init__(self):
        super().__init__(evaluations_table, EvaluationSchema)

    async def get_many_by_app_id(
        self,
        conn: AsyncConnection,
        app_id: int,
        eval_type: EvaluationType,
    ) -> list[EvaluationSchema]:
        """Get all evaluations for a given app_id."""
        stmt = (
            select(self.table)
            .where(
                and_(
                    self.table.c.app_id == app_id,
                    self.table.c.type == eval_type,
                )
            )
            .order_by(self.table.c.created_at.desc())
        )
        result = await conn.execute(stmt)
        rows = result.fetchall()
        if len(rows) == 0:
            return []
        return [
            EvaluationSchema.model_validate(row._mapping)
            for row in rows
        ]
