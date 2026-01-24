from sqlalchemy import select, and_

from src.constants import JudgeType
from src.crud.base import BaseCRUD
from src.db.tables.evaluations import evaluations_table
from src.db.tables.judges import judges_table
from src.schemas.base import UpdateSchema
from src.schemas.evaluation import EvaluationCreateSchema, EvaluationSchema
from src.schemas.judge import JudgeSchema


class EvaluationsCRUD(BaseCRUD[EvaluationCreateSchema, EvaluationSchema, UpdateSchema]):
    """Data access layer for evaluations operations."""

    def __init__(self):
        super().__init__(evaluations_table, EvaluationSchema)

    def get_many_by_eval_run(
        self, eval_run_id: int, judge_type: JudgeType
    ) -> list[JudgeSchema]:
        """Get all judges for a given evaluation run ID filtered by judge type."""
        stmt = (
            select(judges_table)
            .join(
                evaluations_table,
                judges_table.c.evaluation_id == evaluations_table.c.id,
            )
            .where(
                and_(
                    evaluations_table.c.run_id == eval_run_id,
                    judges_table.c.judge_type == judge_type,
                )
            )
            .order_by(judges_table.c.created_at.desc())
        )

        with self.engine.connect() as conn:
            rows = conn.execute(stmt).fetchall()

        if len(rows) == 0:
            return []
        return [JudgeSchema.model_validate(row._mapping) for row in rows]


evaluations_crud = EvaluationsCRUD()
