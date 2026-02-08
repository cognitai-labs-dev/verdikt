import hashlib
from datetime import datetime

from pydantic import BaseModel, Field, model_validator


class PromptVersionCreateSchema(BaseModel):
    app_id: int = Field(description="App this prompt belongs to")
    hash: str | None = Field(
        default=None,
        max_length=64,
        description="SHA-256 hash of the content, don't provide gets calculated",
    )
    content: str = Field(
        description="Prompt content",
    )

    @model_validator(mode="after")
    def generate_hash(self) -> "PromptVersionCreateSchema":
        content_bytes = self.content.encode("utf-8")
        self.hash = hashlib.sha256(content_bytes).hexdigest()
        return self


class PromptVersionSchema(BaseModel):
    id: int = Field(description="Unique identifier")
    app_id: int = Field(description="App this prompt belongs to")
    hash: str = Field(
        max_length=64,
        description="SHA-256 hash of the content",
    )
    content: str = Field(
        description="Prompt content",
    )
    created_at: datetime = Field(
        description=("Timestamp when prompt version was created"),
    )
