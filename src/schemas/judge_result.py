from datetime import datetime

from pydantic import BaseModel, Field


class JudgeResultCreateSchema(BaseModel):
    """DB schema for creating judge results in postgres."""

    evaluation_id: int = Field(description="Foreign key to evaluations table")
    judge_type: str = Field(max_length=50, description="Type of judge")
    judge_model: str | None = Field(
        default=None, max_length=50, description="Model used by judge"
    )
    reasoning: str = Field(description="Reasoning why the score and passed mark")
    passed: bool = Field(description="Whether the evaluation passed")
    score: int = Field(description="Score given by judge")
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


class JudgeResultSchema(JudgeResultCreateSchema):
    """DB schema for reading judge results from postgres."""

    id: int = Field(description="Unique identifier")
    created_at: datetime = Field(description="Timestamp when result was created")
