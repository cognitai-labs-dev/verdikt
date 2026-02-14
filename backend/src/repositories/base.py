from pydantic import BaseModel
from sqlalchemy import Table, delete, insert, select, update
from sqlalchemy.ext.asyncio import AsyncConnection

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

    async def create(
        self, conn: AsyncConnection, data: CreateSchemaT
    ) -> SchemaT:
        stmt = (
            insert(self.table)
            .values(**data.model_dump())
            .returning(self.table)
        )

        result = await conn.execute(stmt)
        row = result.fetchone()
        if row is None:
            raise RuntimeError("create failed")

        return self.schema.model_validate(row._mapping)

    async def create_many(
        self, conn: AsyncConnection, items: list[CreateSchemaT]
    ) -> list[SchemaT]:
        if not items:
            return []

        stmt = (
            insert(self.table)
            .values([item.model_dump() for item in items])
            .returning(self.table)
        )

        result = await conn.execute(stmt)
        return [
            self.schema.model_validate(row._mapping)
            for row in result.fetchall()
        ]

    async def get(
        self, conn: AsyncConnection, row_id: int
    ) -> SchemaT | None:
        stmt = select(self.table).where(self.table.c.id == row_id)
        result = await conn.execute(stmt)
        row = result.fetchone()
        if row is None:
            return None
        return self.schema.model_validate(row._mapping)

    async def delete(
        self, conn: AsyncConnection, row_id: int
    ) -> bool:
        stmt = delete(self.table).where(self.table.c.id == row_id)
        result = await conn.execute(stmt)
        return result.rowcount > 0

    async def get_by_many_ids(
        self, conn: AsyncConnection, ids: list[int]
    ) -> list[SchemaT]:
        if not ids:
            return []

        stmt = select(self.table).where(self.table.c.id.in_(ids))
        result = await conn.execute(stmt)
        return [
            self.schema.model_validate(row._mapping)
            for row in result.fetchall()
        ]

    async def update(
        self, conn: AsyncConnection, data: UpdateSchemaT
    ) -> SchemaT | None:
        values = data.model_dump(exclude_none=True, exclude={"id"})
        if not values:
            return await self.get(conn, data.id)

        stmt = (
            update(self.table)
            .where(self.table.c.id == data.id)
            .values(**values)
            .returning(self.table)
        )

        result = await conn.execute(stmt)
        row = result.fetchone()
        if row is None:
            return None
        return self.schema.model_validate(row._mapping)
