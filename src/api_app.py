from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.v1.router import router
from src.config import Settings
from src.dependencies import db_adpater


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = Settings()
    await db_adpater.connect(settings.postgresql)
    yield
    await db_adpater.disconnect()


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
    app.include_router(router)

    return app
