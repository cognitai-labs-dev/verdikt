from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from src.constants import EvaluationType


class EvaluationCreateSchema(BaseModel):
    app_id: str = Field(
        max_length=100, description="Application identifier"
    )
    app_version: str = Field(
        max_length=50, description="Application version"
    )
    metadata: dict[str, Any] | None = Field(
        default=None, description="Additional metadata"
    )
    type: EvaluationType


class EvaluationSchema(EvaluationCreateSchema):
    id: int = Field(description="Unique identifier")
    created_at: datetime = Field(
        description="Timestamp when evaluation was created"
    )
