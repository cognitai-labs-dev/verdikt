from datetime import datetime

from pydantic import BaseModel, Field


class AppCreateSchema(BaseModel):
    name: str = Field(max_length=100, description="Application name")
    current_prompt_version_id: int


class AppSchema(AppCreateSchema):
    id: int = Field(description="Unique identifier")
    created_at: datetime = Field(
        description="Timestamp when app was created"
    )
