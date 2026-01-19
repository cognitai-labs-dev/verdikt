from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class EvaluationRunCreateSchema(BaseModel):
    """DB schema for creating evaluation runs in postgres."""

    app_id: str = Field(max_length=100, description="Application identifier")
    app_version: str = Field(max_length=50, description="Application version")
    metadata: dict[str, Any] | None = Field(
        default=None, description="Additional metadata"
    )


class EvaluationRunSchema(EvaluationRunCreateSchema):
    """DB schema for reading evaluation runs from postgres."""

    id: int = Field(description="Unique identifier")
    created_at: datetime = Field(description="Timestamp when run was created")
