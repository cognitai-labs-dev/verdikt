from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncConnection

from src.api.v1.router import router
from src.config import APISettings
from src.dependencies import auth_commands, db_adpater, get_connection


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = APISettings()
    await db_adpater.connect(settings.postgres_dsn)
    yield
    await db_adpater.disconnect()


class WellKnownResponse(BaseModel):
    issuer: str


class OpenIDConfigurationResponse(BaseModel):
    token_endpoint: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int


basic = HTTPBasic()


def api_factory():
    app = FastAPI(
        title="AI Evaluation API",
        lifespan=lifespan,
    )
    # TODO: Change for production
    origins = ["*"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get(
        "/.well-known",
        operation_id="getWellKnown",
        tags=["Discovery"],
    )
    async def get_well_known() -> WellKnownResponse:
        # Machine (M2M) issuer = Verdikt itself. Humans never call this; the
        # frontend discovers the login IdP directly.
        settings = APISettings()
        return WellKnownResponse(issuer=settings.SERVICE_BASE_URL)

    @app.get(
        "/.well-known/openid-configuration",
        operation_id="getOpenIDConfiguration",
        tags=["Discovery"],
    )
    async def get_openid_configuration() -> (
        OpenIDConfigurationResponse
    ):
        settings = APISettings()
        return OpenIDConfigurationResponse(
            token_endpoint=f"{settings.SERVICE_BASE_URL}/auth/token"
        )

    @app.post(
        "/auth/token",
        operation_id="postAuthToken",
        tags=["Discovery"],
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
            (
                access_token,
                ttl,
            ) = await auth_commands.issue_machine_token(
                conn, credentials.username, credentials.password
            )
        except ValueError as e:
            raise HTTPException(status_code=401, detail=str(e))
        return TokenResponse(
            access_token=access_token,
            token_type="Bearer",
            expires_in=ttl,
        )

    app.include_router(router)

    return app
