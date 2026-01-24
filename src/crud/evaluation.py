from sqlalchemy import select

from src.crud.base import BaseCRUD
from src.db.tables.evaluations import evaluations_table
from src.schemas.base import UpdateSchema
from src.schemas.evaluation import EvaluationCreateSchema, EvaluationSchema


class EvaluationsCRUD(BaseCRUD[EvaluationCreateSchema, EvaluationSchema, UpdateSchema]):
    """Data access layer for evaluations operations."""

    def __init__(self):
        super().__init__(evaluations_table, EvaluationSchema)

    def get_many_by_app_id(self, app_id: str) -> list[EvaluationSchema]:
        """Get all evaluations for a given app_id."""
        stmt = (
            select(self.table)
            .where(self.table.c.app_id == app_id)
            .order_by(self.table.c.created_at.desc())
        )
        with self.engine.connect() as conn:
            rows = conn.execute(stmt).fetchall()
        if len(rows) == 0:
            return []
        return [EvaluationSchema.model_validate(row._mapping) for row in rows]


evaluations_crud = EvaluationsCRUD()
