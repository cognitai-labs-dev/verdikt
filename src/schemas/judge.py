from datetime import datetime

from pydantic import BaseModel, Field

from src.constants import JudgeType, JudgeStatus
from src.schemas.base import UpdateSchema


class JudgeCreateSchema(BaseModel):
    """DB schema for creating judge in postgres."""

    evaluation_id: int = Field(description="Foreign key to evaluations table")
    judge_type: JudgeType = Field(description="Type of judge")
    judge_model: str = Field(max_length=50, description="Model used by judge")
    status: JudgeStatus
    reasoning: str | None = Field(
        default=None, description="Reasoning why the score and passed mark"
    )
    passed: bool | None = Field(
        default=None, description="Whether the evaluation passed"
    )
    score: int | None = Field(default=None, description="Score given by judge")
    input_tokens: int | None = Field(default=None, description="Number of input tokens")
    output_tokens: int | None = Field(
        default=None, description="Number of output tokens"
    )
    input_tokens_cost: float | None = Field(
        default=None, description="Cost of input tokens"
    )
    output_tokens_cost: float | None = Field(
        default=None, description="Cost of output tokens"
    )


class JudgeSchema(JudgeCreateSchema):
    """DB schema for reading judge from postgres."""

    id: int = Field(description="Unique identifier")
    created_at: datetime = Field(description="Timestamp when result was created")
    updated_at: datetime = Field(description="Timestamp when the row was updated")


class JudgeUpdateSchema(UpdateSchema):
    """Schema for updating a judge."""

    updated_at: datetime = Field(
        default=datetime.now(), description="Timestamp when the row was updated"
    )
    status: JudgeStatus | None = None
    reasoning: str | None = None
    passed: bool | None = None
    score: int | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    input_tokens_cost: float | None = None
    output_tokens_cost: float | None = None
