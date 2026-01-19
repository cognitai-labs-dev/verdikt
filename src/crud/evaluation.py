from sqlalchemy import create_engine, insert

from src.config import settings
from src.db.tables.evaluations import evaluations_table
from src.schemas.evaluation import EvaluationCreateSchema, EvaluationSchema


class EvaluationsCRUD:
    """Data access layer for evaluations operations."""

    def __init__(self):
        self.table = evaluations_table
        self.engine = create_engine(settings.postgresql)

    def create(self, evaluation: EvaluationCreateSchema) -> int:
        stmt = (
            insert(self.table)
            .values(**evaluation.model_dump())
            .returning(self.table.c.id)
        )

        with self.engine.connect() as conn:
            new_id = conn.execute(stmt).fetchone()[0]
            conn.commit()
        return new_id

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


evaluations_crud = EvaluationsCRUD()
