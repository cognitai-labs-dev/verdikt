from datetime import datetime

from pydantic import BaseModel, Field

from src.schemas.judgment import JudgmentCreateSchema


class SampleCreateSchema(BaseModel):
    """DB schema for creating samples in postgres."""

    evaluation_id: int = Field(
        description="Foreign key to evaluations table"
    )
    question: str = Field(description="The question asked")
    human_answer: str = Field(
        description="The answer provided by the human (golden standard)"
    )
    app_answer: str = Field(
        description="The answer provided by the app"
    )
    app_cost: float | None = Field(
        default=None, description="Cost of the application call"
    )


class SampleSchema(SampleCreateSchema):
    """DB schema for reading samples from postgres."""

    id: int = Field(description="Unique identifier")
    created_at: datetime = Field(
        description="Timestamp when sample was created"
    )


class SampleWithJudgmentSchema(SampleSchema, JudgmentCreateSchema):
    """Flat sample + judgment row."""

    judgment_id: int = Field(description="Judgment unique identifier")
    judgment_created_at: datetime = Field(
        description="When judgment was created"
    )
    judgment_updated_at: datetime = Field(
        description="When judgment was updated"
    )
