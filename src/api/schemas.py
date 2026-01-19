from typing import Any

from pydantic import BaseModel, Field


class EvaluationApiSchema(BaseModel):
    question: str = Field(description="The question asked")
    answer: str = Field(description="The answer provided")
    app_cost: float | None = Field(
        default=None, description="Cost of the application call"
    )
    metadata: dict[str, Any] | None = Field(
        default=None, description="Additional metadata"
    )


class EvaluationRunApiSchema(BaseModel):
    app_id: str = Field(max_length=100, description="Application identifier")
    app_version: str = Field(max_length=50, description="Application version")
    metadata: dict[str, Any] | None = Field(
        default=None, description="Additional metadata"
    )
    evaluations: list[EvaluationApiSchema] = Field(description="List of evaluations")
