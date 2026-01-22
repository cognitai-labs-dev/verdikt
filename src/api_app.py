from fastapi import FastAPI

from src.api.v1.router import router
from src.config import settings


def api_factory():
    app = FastAPI(
        title="AI Evaluation API",
        debug=settings.is_dev,
    )

    app.include_router(router)

    return app
