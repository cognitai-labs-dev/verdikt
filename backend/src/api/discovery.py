from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncConnection

from src.config import APISettings
from src.dependencies import auth_commands, get_connection

basic = HTTPBasic()

router = APIRouter(tags=["Discovery"])


class OpenIDConfigurationResponse(BaseModel):
    token_endpoint: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int


@router.get(
    "/.well-known/openid-configuration",
    operation_id="getOpenIDConfiguration",
    summary="OIDC discovery document (token endpoint only)",
    description=(
        "Minimal OpenID Connect discovery document for the machine "
        "issuer. Only `token_endpoint` is published — Verdikt issues "
        "opaque client_credentials tokens and supports no other OIDC "
        "flow (no authorization endpoint, no JWKS: the tokens are not "
        "JWTs). Standard OAuth2 client libraries use this to locate "
        "POST /auth/token. Unauthenticated."
    ),
)
async def get_openid_configuration() -> OpenIDConfigurationResponse:
    settings = APISettings()
    return OpenIDConfigurationResponse(
        token_endpoint=f"{settings.SERVICE_BASE_URL}/auth/token"
    )


@router.post(
    "/auth/token",
    operation_id="postAuthToken",
    summary="Mint a machine token (OAuth2 client_credentials)",
    description=(
        "Exchange machine-client credentials for an opaque bearer "
        "token (`vkt_…`). Credentials are sent via HTTP Basic "
        "(client_id / client_secret — minted on an app's detail page) "
        "and the form field `grant_type` must be `client_credentials`. "
        "The token is stored hashed, expires after MACHINE_TOKEN_TTL "
        "seconds, and dies immediately if the client is revoked. Use "
        "it as `Authorization: Bearer vkt_…` on /v1 routes."
    ),
    responses={
        400: {"description": "unsupported_grant_type"},
        401: {
            "description": "invalid_client — unknown client id, wrong secret, or revoked client"
        },
    },
)
async def post_auth_token(
    credentials: Annotated[HTTPBasicCredentials, Depends(basic)],
    grant_type: Annotated[str, Form()],
    conn: AsyncConnection = Depends(get_connection),
) -> TokenResponse:
    if grant_type != "client_credentials":
        raise HTTPException(
            status_code=400, detail="unsupported_grant_type"
        )
    try:
        access_token, ttl = await auth_commands.issue_machine_token(
            conn, credentials.username, credentials.password
        )
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    return TokenResponse(
        access_token=access_token,
        token_type="Bearer",
        expires_in=ttl,
    )
