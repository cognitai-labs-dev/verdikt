from sqlalchemy import select

from src.crud.base import BaseCRUD
from src.db.tables.samples import samples_table
from src.schemas.base import UpdateSchema
from src.schemas.sample import SampleCreateSchema, SampleSchema


class SamplesCRUD(BaseCRUD[SampleCreateSchema, SampleSchema, UpdateSchema]):
    """Data access layer for samples operations."""

    def __init__(self):
        super().__init__(samples_table, SampleSchema)

    def get_many_by_evaluation(self, evaluation_id: int) -> list[SampleSchema]:
        """Get all samples for a given evaluation ID."""
        stmt = (
            select(samples_table)
            .where(samples_table.c.evaluation_id == evaluation_id)
            .order_by(samples_table.c.created_at.desc())
        )

        with self.engine.connect() as conn:
            rows = conn.execute(stmt).fetchall()

        if len(rows) == 0:
            return []
        return [SampleSchema.model_validate(row._mapping) for row in rows]


samples_crud = SamplesCRUD()
