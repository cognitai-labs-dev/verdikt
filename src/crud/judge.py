from sqlalchemy import create_engine, insert, select, update, and_

from src.config import settings
from src.constants import JudgeStatus, JudgeType
from src.db.tables.judges import judges_table
from src.schemas.judge import JudgeCreateSchema, JudgeSchema, JudgeUpdateSchema


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

    def update(self, data: JudgeUpdateSchema) -> JudgeSchema | None:
        values = data.model_dump(exclude_none=True, exclude={"id"})
        if not values:
            return self.get(data.id)
        stmt = (
            update(self.table)
            .where(self.table.c.id == data.id)
            .values(**values)
            .returning(self.table)
        )
        with self.engine.connect() as conn:
            row = conn.execute(stmt).fetchone()
            conn.commit()
        if row is None:
            return None
        return JudgeSchema.model_validate(row._mapping)


judge_crud = JudgeCRUD()
