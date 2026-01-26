from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.v1.router import router
from src.config import settings


def api_factory():
    app = FastAPI(
        title="AI Evaluation API",
        debug=settings.is_dev,
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
