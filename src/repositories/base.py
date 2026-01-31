from pydantic import BaseModel
from sqlalchemy import Table, create_engine, insert, select, update

from src.config import settings
from src.schemas.base import UpdateSchema


class BaseRepository[
    CreateSchemaT: BaseModel,
    SchemaT: BaseModel,
    UpdateSchemaT: UpdateSchema,
]:
    """Generic base class for data access operations using SQLAlchemy Core."""

    def __init__(self, table: Table, schema: type[SchemaT]):
        self.table = table
        self.schema = schema
        self.engine = create_engine(settings.postgresql)

    def create(self, data: CreateSchemaT) -> SchemaT:
        stmt = insert(self.table).values(**data.model_dump()).returning(self.table)

        with self.engine.connect() as conn:
            row = conn.execute(stmt).fetchone()
            conn.commit()
        if row is None:
            raise RuntimeError("create failed")

        return self.schema.model_validate(row._mapping)

    def create_many(self, items: list[CreateSchemaT]) -> list[SchemaT]:
        if not items:
            return []

        stmt = (
            insert(self.table)
            .values([item.model_dump() for item in items])
            .returning(self.table)
        )

        with self.engine.connect() as conn:
            result = conn.execute(stmt)
            rows = [
                self.schema.model_validate(row._mapping) for row in result.fetchall()
            ]
            conn.commit()
        return rows

    def get(self, row_id: int) -> SchemaT | None:
        stmt = select(self.table).where(self.table.c.id == row_id)
        with self.engine.connect() as conn:
            row = conn.execute(stmt).fetchone()
        if row is None:
            return None
        return self.schema.model_validate(row._mapping)

    def update(self, data: UpdateSchemaT) -> SchemaT | None:
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
        return self.schema.model_validate(row._mapping)
