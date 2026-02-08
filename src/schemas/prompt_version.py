from datetime import datetime

from pydantic import BaseModel, Field


class PromptVersionCreateSchema(BaseModel):
    app_id: int = Field(description="App this prompt belongs to")
    content: str = Field(
        description="Prompt content",
    )


class PromptVersionSchema(BaseModel):
    id: int = Field(description="Unique identifier")
    app_id: int = Field(description="App this prompt belongs to")
    content: str = Field(
        description="Prompt content",
    )
    created_at: datetime = Field(
        description=("Timestamp when prompt version was created"),
    )
