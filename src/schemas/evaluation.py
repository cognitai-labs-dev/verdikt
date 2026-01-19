from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class EvaluationCreateSchema(BaseModel):
    """DB schema for creating evaluations in postgres."""

    run_id: int = Field(description="Foreign key to evaluation_runs table")
    question: str = Field(description="The question asked")
    answer: str = Field(description="The answer provided")
    app_cost: float | None = Field(default=None, description="Cost of the application call")
    metadata: dict[str, Any] | None = Field(default=None, description="Additional metadata")


class EvaluationSchema(EvaluationCreateSchema):
    """DB schema for reading evaluations from postgres."""

    id: int = Field(description="Unique identifier")
    created_at: datetime = Field(description="Timestamp when evaluation was created")
