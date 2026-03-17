from fastapi import APIRouter

from backend.api.v1.auth import router as auth_router
from backend.api.v1.health import router as health_router
from backend.api.v1.invoke import router as invoke_router
from backend.api.v1.logs import router as logs_router
from backend.api.v1.nodes import router as nodes_router
from backend.api.v1.search import router as search_router
from backend.api.v1.stats import router as stats_router
from backend.api.v1.tags import router as tags_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(auth_router)
api_router.include_router(nodes_router)
api_router.include_router(invoke_router)
api_router.include_router(logs_router)
api_router.include_router(search_router)
api_router.include_router(stats_router)
api_router.include_router(tags_router)
