from sqlalchemy import create_engine, insert

from src.config import settings
from src.db.tables.evaluation_runs import evaluation_runs_table
from src.schemas.evaluation_run import EvaluationRunCreateSchema


class EvaluationRunsCRUD:
    """Data access layer for evaluation runs operations."""

    def __init__(self):
        self.table = evaluation_runs_table
        self.engine = create_engine(settings.postgresql)

    def create(self, evaluation_run: EvaluationRunCreateSchema) -> int:
        stmt = (
            insert(self.table)
            .values(**evaluation_run.model_dump())
            .returning(self.table.c.id)
        )

        with self.engine.connect() as conn:
            new_id = conn.execute(stmt).fetchone()[0]
            conn.commit()
        return new_id


evaluation_runs_crud = EvaluationRunsCRUD()
