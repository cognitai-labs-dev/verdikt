from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.api.v1.router import router
from src.config import APISettings
from src.dependencies import db_adpater


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = APISettings()
    await db_adpater.connect(settings.postgres_dsn)
    yield
    await db_adpater.disconnect()


class WellKnownResponse(BaseModel):
    issuer: str


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
        settings = APISettings()
        return WellKnownResponse(issuer=settings.zitadel_issuer)

    app.include_router(router)

    return app
