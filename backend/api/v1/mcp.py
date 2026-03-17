"""
MCP SSE 路由 (5.3)

将 NodeVault MCP Server 以 SSE subapp 形式挂载到 FastAPI。
访问路径：GET /mcp/sse  （FastMCP sse_app 的默认 SSE 端点）
"""
from __future__ import annotations

from fastapi import APIRouter

from backend.core.exporter.mcp_server import create_mcp_server

router = APIRouter(tags=["MCP"])

# 懒加载 mcp 实例（避免进程启动时就连接 DB）
_mcp_instance = None


def get_mcp_app():
    global _mcp_instance
    if _mcp_instance is None:
        _mcp_instance = create_mcp_server()
    return _mcp_instance.sse_app()
