from typing import Any

from pydantic import BaseModel, Field

from src.constants import EvaluationType


class SampleApiSchema(BaseModel):
    question: str = Field(description="The question asked")
    human_answer: str = Field(
        description="The answer provided by the human"
    )
    app_answer: str = Field(
        description="The answer provided by the app"
    )
    app_cost: float | None = Field(
        default=None, description="Cost of the application call"
    )
    metadata: dict[str, Any] | None = Field(
        default=None, description="Additional metadata"
    )


class EvaluationApiSchema(BaseModel):
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
    samples: list[SampleApiSchema] = Field(
        description="List of samples"
    )
