import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.discovery import router as discovery_router
from src.api.v1.router import router
from src.config import APISettings
from src.dependencies import admin_registry, db_adpater

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = APISettings()
    await db_adpater.connect(settings.postgres_dsn)
    if settings.ACCESS_CONFIG_PATH:
        logger.info(
            "access config: loading '%s'", settings.ACCESS_CONFIG_PATH
        )
        cfg = admin_registry.load(settings.ACCESS_CONFIG_PATH)
        async with db_adpater.engine.begin() as conn:
            await admin_registry.reconcile(conn, cfg)
    else:
        logger.info(
            "access config: ACCESS_CONFIG_PATH not set — skipping "
            "reconciliation (no admins, no email bindings configured)"
        )
    yield
    await db_adpater.disconnect()


def api_factory():
    app = FastAPI(
        title="AI Evaluation API",
        lifespan=lifespan,
    )
    # The frontend BFF reaches this API server-to-server (no browser CORS), so
    # cross-origin is locked down by default. Set CORS_ORIGINS to opt specific
    # browser origins in.
    origins = APISettings().cors_origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=bool(origins),
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(discovery_router)
    app.include_router(router)

    return app
