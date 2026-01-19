from sqlalchemy import create_engine, insert, select

from src.config import settings
from src.db.tables.judges import judges_table
from src.schemas.judge import JudgeCreateSchema, JudgeSchema


class JudgeCRUD:
    """Data access layer for judge operations."""

    def __init__(self):
        self.table = judges_table
        self.engine = create_engine(settings.postgresql)

    def create(self, judge: JudgeCreateSchema) -> int:
        stmt = (
            insert(self.table).values(**judge.model_dump()).returning(self.table.c.id)
        )

        with self.engine.connect() as conn:
            new_id = conn.execute(stmt).fetchone()[0]
            conn.commit()
        return new_id

    def get(self, judge_id: int) -> JudgeSchema | None:
        stmt = select(self.table).where(self.table.c.id == judge_id)
        with self.engine.connect() as conn:
            row = conn.execute(stmt).fetchone()
        if row is None:
            return None
        return JudgeSchema.model_validate(row._mapping)


judge_crud = JudgeCRUD()
