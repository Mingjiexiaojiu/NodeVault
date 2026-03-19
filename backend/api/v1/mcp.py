"""
MCP SSE 路由 (5.3)

将 NodeVault MCP Server 以 SSE subapp 形式挂载到 FastAPI。
访问路径：GET /mcp/sse  （FastMCP sse_app 的默认 SSE 端点）

认证：在连接时传递 API Key，支持两种方式：
  - Query param: /mcp/sse?api_key=nvk_xxx
  - Header: X-API-Key: nvk_xxx
"""
from __future__ import annotations

import hashlib

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from sqlalchemy import select

from backend.core.exporter.mcp_server import create_mcp_server
from backend.database.session import async_session_factory
from backend.models.api_key import ApiKey

router = APIRouter(tags=["MCP"])

_mcp_instance = None


def get_mcp_app():
    global _mcp_instance
    if _mcp_instance is None:
        _mcp_instance = create_mcp_server()
    return _mcp_instance.sse_app()


async def _validate_mcp_token(request: Request) -> bool:
    """从 query param 或 header 中提取并验证 API Key"""
    api_key_str = (
        request.query_params.get("api_key")
        or request.headers.get("x-api-key")
    )
    if not api_key_str or not api_key_str.startswith("nvk_"):
        return False

    key_hash = hashlib.sha256(api_key_str.encode()).hexdigest()
    async with async_session_factory() as db:
        result = await db.execute(
            select(ApiKey).where(ApiKey.key_hash == key_hash, ApiKey.is_active.is_(True))
        )
        return result.scalar_one_or_none() is not None


class MCPAuthMiddleware:
    """为 MCP SSE 子应用增加 API Key 鉴权的 ASGI 中间件"""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] in ("http", "websocket"):
            request = Request(scope, receive)
            if not await _validate_mcp_token(request):
                response = JSONResponse(
                    {"error": "Unauthorized: provide a valid API Key via ?api_key=nvk_xxx or X-API-Key header"},
                    status_code=401,
                )
                await response(scope, receive, send)
                return
        await self.app(scope, receive, send)


def get_mcp_app_with_auth():
    return MCPAuthMiddleware(get_mcp_app())
