from sqlalchemy import create_engine, insert, select

from src.config import settings
from src.db.tables.judge_results import judge_results_table
from src.schemas.judge_result import JudgeResultCreateSchema, JudgeResultSchema


class JudgeResultsCRUD:
    """Data access layer for judge results operations."""

    def __init__(self):
        self.table = judge_results_table
        self.engine = create_engine(settings.postgresql)

    def create(self, judge_result: JudgeResultCreateSchema) -> int:
        stmt = (
            insert(self.table)
            .values(**judge_result.model_dump())
            .returning(self.table.c.id)
        )

        with self.engine.connect() as conn:
            new_id = conn.execute(stmt).fetchone()[0]
            conn.commit()
        return new_id

    def get(self, judge_id: int) -> JudgeResultSchema | None:
        stmt = select(self.table).where(self.table.c.id == judge_id)
        with self.engine.connect() as conn:
            row = conn.execute(stmt).fetchone()
        if row is None:
            return None
        return JudgeResultSchema.model_validate(row._mapping)


judge_results_crud = JudgeResultsCRUD()
