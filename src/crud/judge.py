from sqlalchemy import select, and_

from src.constants import JudgeStatus, JudgeType
from src.crud.base import BaseCRUD
from src.db.tables.judges import judges_table
from src.schemas.judge import JudgeCreateSchema, JudgeSchema, JudgeUpdateSchema


class JudgeCRUD(BaseCRUD[JudgeCreateSchema, JudgeSchema, JudgeUpdateSchema]):
    """Data access layer for judge operations."""

    def __init__(self):
        super().__init__(judges_table, JudgeSchema)

    def get_many_pending(self, limit: int) -> list[JudgeSchema]:
        stmt = (
            select(self.table)
            .where(
                and_(
                    self.table.c.status == JudgeStatus.PENDING,
                    self.table.c.judge_type == JudgeType.LLM,
                )
            )
            .order_by(self.table.c.created_at.desc())
            .limit(limit)
        )

        with self.engine.connect() as conn:
            rows = conn.execute(stmt).fetchall()

        if len(rows) == 0:
            return []
        return [JudgeSchema.model_validate(row._mapping) for row in rows]

    def get_many_by_eval_id(
        self, evaluation_id: int, judge_type: JudgeType
    ) -> JudgeSchema | None:
        """Get all judges for a given evaluation ID filtered by judge type."""
        stmt = (
            select(self.table)
            .where(
                and_(
                    self.table.c.evaluation_id == evaluation_id,
                    self.table.c.judge_type == judge_type,
                )
            )
            .order_by(self.table.c.created_at.desc())
        )

        with self.engine.connect() as conn:
            rows = conn.execute(stmt).fetchall()

        if len(rows) == 0:
            return None
        if len(rows) > 1:
            raise RuntimeError("More then 1 judge for an eval")

        return JudgeSchema.model_validate(rows[0]._mapping)


judge_crud = JudgeCRUD()
