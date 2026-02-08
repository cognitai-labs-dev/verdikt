from fastapi import APIRouter

from src.api.v1.response import ORJsonResponse
from src.api.v1.routes.app import router as app_router
from src.api.v1.routes.evaluation import router as evaluation_router
from src.api.v1.routes.sample import router as sample_router

router = APIRouter(
    prefix="/v1", default_response_class=ORJsonResponse
)

router.include_router(app_router)
router.include_router(sample_router)
router.include_router(evaluation_router)
