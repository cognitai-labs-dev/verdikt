from pydantic import BaseModel, Field


class UpdateSchema(BaseModel):
    """Base schema for update operations containing the id field."""

    id: int = Field(description="Unique identifier of the record to update")
