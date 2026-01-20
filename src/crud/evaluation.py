from sqlalchemy import create_engine, insert, select

from src.config import settings
from src.db.tables.evaluations import evaluations_table
from src.schemas.evaluation import EvaluationCreateSchema, EvaluationSchema


class EvaluationsCRUD:
    """Data access layer for evaluations operations."""

    def __init__(self):
        self.table = evaluations_table
        self.engine = create_engine(settings.postgresql)

    def create_many(
        self, evaluations: list[EvaluationCreateSchema]
    ) -> list[EvaluationSchema]:
        if not evaluations:
            return []

        stmt = (
            insert(self.table)
            .values([e.model_dump() for e in evaluations])
            .returning(self.table)
        )

        with self.engine.connect() as conn:
            result = conn.execute(stmt)
            rows = [EvaluationSchema(**row._mapping) for row in result.fetchall()]
            conn.commit()
        return rows

    def get(self, evaluation_id: int) -> EvaluationSchema | None:
        stmt = select(self.table).where(self.table.c.id == evaluation_id)
        with self.engine.connect() as conn:
            row = conn.execute(stmt).fetchone()
        if row is None:
            return None
        return EvaluationSchema.model_validate(row._mapping)


evaluations_crud = EvaluationsCRUD()
