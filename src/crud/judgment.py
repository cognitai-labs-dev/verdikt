from sqlalchemy import select, and_

from src.constants import JudgmentStatus, JudgmentType
from src.crud.base import BaseCRUD
from src.db.tables.judgments import judgments_table
from src.schemas.judgment import (
    JudgmentCreateSchema,
    JudgmentSchema,
    JudgmentUpdateSchema,
)


class JudgmentCRUD(
    BaseCRUD[JudgmentCreateSchema, JudgmentSchema, JudgmentUpdateSchema]
):
    """Data access layer for judgment operations."""

    def __init__(self):
        super().__init__(judgments_table, JudgmentSchema)

    def get_many_pending(self, limit: int) -> list[JudgmentSchema]:
        stmt = (
            select(self.table)
            .where(
                and_(
                    self.table.c.status == JudgmentStatus.PENDING,
                    self.table.c.judgment_type == JudgmentType.LLM,
                )
            )
            .order_by(self.table.c.created_at.desc())
            .limit(limit)
        )

        with self.engine.connect() as conn:
            rows = conn.execute(stmt).fetchall()

        if len(rows) == 0:
            return []
        return [JudgmentSchema.model_validate(row._mapping) for row in rows]

    def get_many_by_sample_id(
        self, sample_id: int, judgment_type: JudgmentType
    ) -> list[JudgmentSchema]:
        """Get all judgments for a given sample ID filtered by judgment type."""
        stmt = (
            select(self.table)
            .where(
                and_(
                    self.table.c.sample_id == sample_id,
                    self.table.c.judgment_type == judgment_type,
                )
            )
            .order_by(self.table.c.created_at.desc())
        )

        with self.engine.connect() as conn:
            rows = conn.execute(stmt).fetchall()

        if len(rows) == 0:
            return []
        return [JudgmentSchema.model_validate(row._mapping) for row in rows]


judgment_crud = JudgmentCRUD()
