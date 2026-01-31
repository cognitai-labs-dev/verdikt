from datetime import datetime

from pydantic import BaseModel, Field

from src.constants import JudgmentType, JudgmentStatus
from src.schemas.base import UpdateSchema


class JudgmentCreateSchema(BaseModel):
    """DB schema for creating judgment in postgres."""

    sample_id: int = Field(description="Foreign key to samples table")
    judgment_type: JudgmentType = Field(
        description="Type of judgment"
    )
    judgment_model: str = Field(
        max_length=50, description="Model used by judge"
    )
    status: JudgmentStatus
    reasoning: str | None = Field(
        default=None,
        description="Reasoning why the score and passed mark",
    )
    passed: bool | None = Field(
        default=None, description="Whether the evaluation passed"
    )
    input_tokens: int | None = Field(
        default=None, description="Number of input tokens"
    )
    output_tokens: int | None = Field(
        default=None, description="Number of output tokens"
    )
    input_tokens_cost: float | None = Field(
        default=None, description="Cost of input tokens"
    )
    output_tokens_cost: float | None = Field(
        default=None, description="Cost of output tokens"
    )


class JudgmentSchema(JudgmentCreateSchema):
    """DB schema for reading judgment from postgres."""

    id: int = Field(description="Unique identifier")
    created_at: datetime = Field(
        description="Timestamp when result was created"
    )
    updated_at: datetime = Field(
        description="Timestamp when the row was updated"
    )


class JudgmentUpdateSchema(UpdateSchema):
    """Schema for updating a judgment."""

    updated_at: datetime = Field(
        default=datetime.now(),
        description="Timestamp when the row was updated",
    )
    status: JudgmentStatus | None = None
    reasoning: str | None = None
    passed: bool | None = None
    score: int | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    input_tokens_cost: float | None = None
    output_tokens_cost: float | None = None
