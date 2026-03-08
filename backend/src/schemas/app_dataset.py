from datetime import datetime

from pydantic import BaseModel, Field

from src.schemas.base import UpdateSchema


class AppDatasetCreateSchema(BaseModel):
    """DB schema for creating an app dataset entry."""

    question: str = Field(description="Question text")
    human_answer: str = Field(description="Human-provided answer")
    app_id: int = Field(description="Foreign key to apps table")


class AppDatasetSchema(AppDatasetCreateSchema):
    """DB schema for reading an app dataset entry."""

    id: int = Field(description="Unique identifier")
    created_at: datetime = Field(
        description="Timestamp when entry was created"
    )
    updated_at: datetime = Field(
        description="Timestamp when entry was updated"
    )


class AppDatasetUpdateSchema(UpdateSchema):
    """Schema for updating an app dataset entry."""

    question: str | None = None
    human_answer: str | None = None
    updated_at: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp when the row was updated",
    )
