from datetime import datetime

from pydantic import BaseModel, Field

from src.schemas.base import UpdateSchema


class MachineClientCreateSchema(BaseModel):
    client_id: str = Field(description="Public client identifier")
    client_secret_hash: str = Field(
        description="SHA-256 hex of the client secret"
    )
    name: str = Field(
        max_length=100, description="Human-readable label"
    )
    is_admin: bool = Field(
        default=False,
        description="Whether the client may access every app",
    )


class MachineClientSchema(MachineClientCreateSchema):
    id: int = Field(description="Unique identifier")
    revoked: bool = Field(description="Whether the client is revoked")
    created_at: datetime = Field(description="Timestamp when created")


class MachineClientUpdateSchema(UpdateSchema):
    revoked: bool | None = None
