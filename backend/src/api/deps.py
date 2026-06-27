import logging
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncConnection

from src.api.auth import TokenVerifier
from src.auth.commands import TOKEN_PREFIX
from src.auth.hashing import sha256_hex, utcnow
from src.config import APISettings
from src.constants import SubjectType
from src.dependencies import (
    app_principal_repo,
    evaluation_repo,
    get_connection,
    machine_client_repo,
    machine_token_repo,
    sample_repo,
)

security = HTTPBearer()
token_verifier = TokenVerifier()
logger = logging.getLogger(__name__)


class Principal(BaseModel):
    """Unified caller identity — a human (email) or a machine (client_id)."""

    subject: str
    subject_type: SubjectType
    is_admin: bool


async def decoded_jwt_token(
    auth: Annotated[HTTPAuthorizationCredentials, Depends(security)],
):
    try:
        return await token_verifier.decoded_token(auth.credentials)
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=401, detail="Invalid or expired token"
        )


async def authenticate(
    auth: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    conn: AsyncConnection = Depends(get_connection),
) -> Principal:
    """Resolve a bearer token to a Principal — machine or human."""
    token = auth.credentials

    if token.startswith(TOKEN_PREFIX):
        machine_token = await machine_token_repo.get_by_hash(
            conn, sha256_hex(token)
        )
        if (
            machine_token is None
            or machine_token.revoked
            or machine_token.expires_at < utcnow()
        ):
            raise HTTPException(
                status_code=401, detail="Invalid or expired token"
            )
        client = await machine_client_repo.get_by_client_id(
            conn, machine_token.client_id
        )
        if client is None or client.revoked:
            raise HTTPException(
                status_code=401, detail="Invalid or expired token"
            )
        return Principal(
            subject=client.client_id,
            subject_type=SubjectType.CLIENT,
            is_admin=client.is_admin,
        )

    try:
        claims = await token_verifier.decoded_token(token)
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=401, detail="Invalid or expired token"
        )
    email = claims.get("email", "")
    return Principal(
        subject=email,
        subject_type=SubjectType.EMAIL,
        is_admin=email in APISettings().admin_emails,
    )


async def allowed_app_ids(
    conn: AsyncConnection, principal: Principal
) -> list[int] | None:
    """App ids the principal may access. `None` means every app (admin)."""
    if principal.is_admin:
        return None
    return await app_principal_repo.app_ids_for(
        conn, principal.subject_type, principal.subject
    )


def _forbidden() -> HTTPException:
    return HTTPException(status_code=403, detail="Forbidden")


async def _assert_app_access(
    conn: AsyncConnection, principal: Principal, app_id: int
) -> None:
    ids = await allowed_app_ids(conn, principal)
    if ids is not None and app_id not in ids:
        raise _forbidden()


async def require_app_access(
    app_id: int,
    principal: Principal = Depends(authenticate),
    conn: AsyncConnection = Depends(get_connection),
) -> Principal:
    """Guard for `/app/{app_id}/...` routes."""
    await _assert_app_access(conn, principal, app_id)
    return principal


async def require_evaluation_access(
    evaluation_id: int,
    principal: Principal = Depends(authenticate),
    conn: AsyncConnection = Depends(get_connection),
) -> Principal:
    """Resolve evaluation -> owning app, then check access."""
    evaluation = await evaluation_repo.get(conn, evaluation_id)
    if evaluation is None:
        raise HTTPException(
            status_code=404, detail="Evaluation not found"
        )
    await _assert_app_access(conn, principal, evaluation.app_id)
    return principal


async def require_sample_access(
    sample_id: int,
    principal: Principal = Depends(authenticate),
    conn: AsyncConnection = Depends(get_connection),
) -> Principal:
    """Resolve sample -> evaluation -> owning app, then check access."""
    sample = await sample_repo.get(conn, sample_id)
    if sample is None:
        raise HTTPException(
            status_code=404, detail="Sample not found"
        )
    evaluation = await evaluation_repo.get(conn, sample.evaluation_id)
    if evaluation is None:
        raise HTTPException(
            status_code=404, detail="Evaulation not found"
        )
    await _assert_app_access(conn, principal, evaluation.app_id)
    return principal
