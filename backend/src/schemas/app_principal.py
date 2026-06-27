from pydantic import BaseModel, Field

from src.constants import SubjectType
from src.schemas.base import UpdateSchema


class AppPrincipalCreateSchema(BaseModel):
    app_id: int = Field(description="App the principal is bound to")
    subject_type: SubjectType = Field(description="email or client")
    subject: str = Field(description="Email or client_id")


class AppPrincipalSchema(AppPrincipalCreateSchema):
    id: int = Field(description="Unique identifier")


class AppPrincipalUpdateSchema(UpdateSchema):
    pass
