from datetime import datetime

from pydantic import BaseModel, Field

from src.schemas.base import UpdateSchema


class MachineTokenCreateSchema(BaseModel):
    token_hash: str = Field(
        description="SHA-256 hex of the opaque token"
    )
    client_id: str = Field(description="Owning machine client")
    expires_at: datetime = Field(description="Token expiry timestamp")
    revoked: bool = Field(
        default=False, description="Whether revoked"
    )


class MachineTokenSchema(MachineTokenCreateSchema):
    id: int = Field(description="Unique identifier")
    created_at: datetime = Field(description="Timestamp when created")


class MachineTokenUpdateSchema(UpdateSchema):
    revoked: bool | None = None
