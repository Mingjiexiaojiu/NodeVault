from fastapi import APIRouter

from backend.api.v1.agent import router as agent_router
from backend.api.v1.ai_configs import router as ai_configs_router
from backend.api.v1.auth import router as auth_router
from backend.api.v1.credentials import router as credentials_router
from backend.api.v1.departments import router as departments_router
from backend.api.v1.discovery import router as discovery_router
from backend.api.v1.export import router as export_router
from backend.api.v1.health import router as health_router
from backend.api.v1.invoke import router as invoke_router
from backend.api.v1.logs import router as logs_router
from backend.api.v1.nodes import router as nodes_router
from backend.api.v1.search import router as search_router
from backend.api.v1.skills import router as skills_router
from backend.api.v1.stats import router as stats_router
from backend.api.v1.tags import router as tags_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(auth_router)
api_router.include_router(ai_configs_router)
api_router.include_router(credentials_router)
api_router.include_router(departments_router)
api_router.include_router(discovery_router)
api_router.include_router(nodes_router)
api_router.include_router(export_router)
api_router.include_router(invoke_router)
api_router.include_router(logs_router)
api_router.include_router(search_router)
api_router.include_router(skills_router)
api_router.include_router(stats_router)
api_router.include_router(tags_router)
api_router.include_router(agent_router)
