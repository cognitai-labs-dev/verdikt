from fastapi import APIRouter, Depends

from src.api.deps import Principal, authenticate
from src.api.v1.response import ORJsonResponse
from src.api.v1.schemas import MeResponse

router = APIRouter(
    prefix="/me",
    tags=["Me"],
    default_response_class=ORJsonResponse,
)


@router.get(
    "",
    operation_id="getMe",
    description="Return the authenticated principal's identity",
)
async def get_me(
    principal: Principal = Depends(authenticate),
) -> MeResponse:
    return MeResponse(
        subject=principal.subject,
        subject_type=principal.subject_type,
        is_admin=principal.is_admin,
    )
