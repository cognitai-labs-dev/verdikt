from src.db.tables.evaluations import evaluations_table
from src.repositories.base import BaseRepository
from src.schemas.app import AppCreateSchema, AppSchema
from src.schemas.base import UpdateSchema


class AppsRepository(
    BaseRepository[AppCreateSchema, AppSchema, UpdateSchema]
):
    """Data access layer for apps operations."""

    def __init__(self):
        super().__init__(evaluations_table, AppSchema)
