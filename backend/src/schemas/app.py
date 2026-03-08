import re
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from src.schemas.base import UpdateSchema

_SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class AppCreateSchema(BaseModel):
    name: str = Field(max_length=100, description="Application name")
    slug: str = Field(
        max_length=100,
        description="URL-safe identifier (lowercase, alphanumeric, hyphens)",
    )
    current_prompt_version_id: int | None = None

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        if not _SLUG_RE.match(v):
            raise ValueError(
                "slug must be lowercase alphanumeric with hyphens only (e.g. 'my-app')"
            )
        return v


class AppSchema(AppCreateSchema):
    id: int = Field(description="Unique identifier")
    created_at: datetime = Field(
        description="Timestamp when app was created"
    )


class AppUpdateSchema(UpdateSchema):
    current_prompt_version_id: int | None = None
