from src.db.tables.prompt_versions import (
    prompt_versions_table,
)
from src.repositories.base import BaseRepository
from src.schemas.base import UpdateSchema
from src.schemas.prompt_version import (
    PromptVersionCreateSchema,
    PromptVersionSchema,
)


class PromptVersionRepository(
    BaseRepository[
        PromptVersionCreateSchema,
        PromptVersionSchema,
        UpdateSchema,
    ]
):
    """Data access layer for prompt versions."""

    def __init__(self):
        super().__init__(prompt_versions_table, PromptVersionSchema)
