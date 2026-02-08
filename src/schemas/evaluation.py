from datetime import datetime

from pydantic import BaseModel, Field

from src.constants import EvaluationType


class EvaluationCreateSchema(BaseModel):
    app_id: int = Field(description="Application identifier")
    type: EvaluationType
    version: str
    prompt_version_id: int


class EvaluationSchema(EvaluationCreateSchema):
    id: int = Field(description="Unique identifier")
    created_at: datetime = Field(
        description="Timestamp when evaluation was created"
    )
