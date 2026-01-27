from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class SampleCreateSchema(BaseModel):
    """DB schema for creating samples in postgres."""

    evaluation_id: int = Field(description="Foreign key to evaluations table")
    question: str = Field(description="The question asked")
    human_answer: str = Field(
        description="The answer provided by the human (golden standard)"
    )
    app_answer: str = Field(description="The answer provided by the app")
    app_cost: float | None = Field(
        default=None, description="Cost of the application call"
    )
    metadata: dict[str, Any] | None = Field(
        default=None, description="Additional metadata"
    )


class SampleSchema(SampleCreateSchema):
    """DB schema for reading samples from postgres."""

    id: int = Field(description="Unique identifier")
    created_at: datetime = Field(description="Timestamp when sample was created")
