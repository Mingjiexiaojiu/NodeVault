"""
Agent 接口：能力发现、批量工具获取、OpenAI tool_call 代理执行 (4.1–4.5)
"""
from __future__ import annotations

import json
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.deps import get_current_user
from backend.core.exporter import LangChainExporter, OpenAIExporter
from backend.core.invocation import NodeNotFoundError, NodeVersionNotFoundError, invoke_node_by_name
from backend.core.registry import NodeRegistry
from backend.core.search import NodeSearchIndex
from backend.database.session import get_db
from backend.models.node import Node, NodeVersion
from backend.models.user import User
from backend.schemas.enums import NodeStatus
from backend.schemas.response import ApiResponse

router = APIRouter(prefix="/agent", tags=["Agent"])

# ---- helpers ----------------------------------------------------------------

def _node_to_dict(node: Any, tags: list[str] | None = None) -> dict[str, Any]:
    return {
        "id": str(node.id) if hasattr(node, "id") else str(node.get("id", "")),
        "name": node.name if hasattr(node, "name") else node.get("name", ""),
        "display_name": node.display_name if hasattr(node, "display_name") else node.get("display_name"),
        "description": node.description if hasattr(node, "description") else node.get("description"),
        "category": (node.category_rel.display_name if node.category_rel else None) if hasattr(node, "category_rel") else node.get("category"),
        "tags": tags or ([t.tag for t in node.tags] if hasattr(node, "tags") else node.get("tags") or []),
    }


def _version_to_dict(version: NodeVersion) -> dict[str, Any]:
    return {
        "version": version.version,
        "input_schema": version.input_schema,
        "output_schema": version.output_schema,
    }


async def _enrich_with_versions(
    hits: list[dict[str, Any]],
    db: AsyncSession,
    registry: NodeRegistry,
) -> list[dict[str, Any]]:
    """为搜索命中结果补充 version 信息"""
    items: list[dict[str, Any]] = []
    for hit in hits:
        try:
            node_id = uuid.UUID(str(hit["id"]))
        except (KeyError, ValueError):
            continue
        version = await registry.get_version(node_id)
        if version is None:
            continue
        items.append({
            "node": {
                "id": hit["id"],
                "name": hit.get("name", ""),
                "display_name": hit.get("display_name"),
                "description": hit.get("description"),
                "type": hit.get("type"),
                "category": hit.get("category"),
                "tags": hit.get("tags") or [],
            },
            "version": _version_to_dict(version),
        })
    return items


# ---- /discover --------------------------------------------------------------

@router.get("/discover", response_model=ApiResponse)
async def discover_capabilities(
    intent: str = Query(..., description="自然语言描述需求，如'分析交易风险'"),
    limit: int = Query(5, ge=1, le=20),
    format: str = Query("openai", enum=["openai", "langchain", "mcp", "raw"]),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse:
    """Agent 能力发现：自然语言意图 → 匹配 Node 列表"""
    search_index = NodeSearchIndex()
    try:
        raw = search_index.search(
            query=intent,
            filters={"status": NodeStatus.ACTIVE.value},
            page_size=limit * 2,
        )
        hits = raw.get("hits", [])
    except Exception:
        hits = []

    registry = NodeRegistry(db)
    items = await _enrich_with_versions(hits, db, registry)
    items = items[:limit]

    if format == "openai":
        return ApiResponse(data={"tools": OpenAIExporter().export_nodes(items)})
    elif format == "langchain":
        return ApiResponse(data={"code": LangChainExporter().export_nodes(items)})
    elif format == "mcp":
        oe = OpenAIExporter()
        mcp_tools = [
            {
                "name": oe._safe_name(item["node"]["name"]),
                "description": item["node"].get("description") or "",
                "inputSchema": item["version"]["input_schema"],
            }
            for item in items
        ]
        return ApiResponse(data={"tools": mcp_tools})
    else:  # raw
        return ApiResponse(data={"nodes": items})


# ---- /tools -----------------------------------------------------------------

@router.get("/tools", response_model=ApiResponse)
async def get_all_tools(
    tags: list[str] = Query(default=[]),
    type: str | None = Query(default=None),
    namespace: str | None = Query(default=None),
    limit: int = Query(100, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse:
    """获取所有可用 Node 的 OpenAI Tools 格式（Agent 启动时批量拉取）"""
    registry = NodeRegistry(db)
    nodes = await registry.list_nodes(
        owner=current_user,
        status=NodeStatus.ACTIVE.value,
        type=type,
        page_size=limit,
    )

    # 按 tag 过滤
    if tags:
        tag_set = set(tags)
        nodes = [n for n in nodes if tag_set.intersection({t.tag for t in (n.tags or [])})]

    items: list[dict[str, Any]] = []
    for node in nodes:
        version = await registry.get_version(node.id)
        if version is None:
            continue
        items.append({"node": _node_to_dict(node), "version": _version_to_dict(version)})

    return ApiResponse(data={"tools": OpenAIExporter().export_nodes(items)})


# ---- /execute-tool ----------------------------------------------------------

class ToolCallFunction(BaseModel):
    name: str
    arguments: str  # JSON string，与 OpenAI 格式一致


class ToolCallRequest(BaseModel):
    id: str
    type: str = "function"
    function: ToolCallFunction


@router.post("/execute-tool", response_model=ApiResponse)
async def execute_tool(
    tool_call: ToolCallRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse:
    """
    代理执行 OpenAI tool_call 对象，路由到对应 Node 执行，
    返回 OpenAI tool result 格式。
    """
    try:
        arguments = json.loads(tool_call.function.arguments)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid JSON in function.arguments: {exc}",
        )

    try:
        result = await invoke_node_by_name(
            name=tool_call.function.name,
            arguments=arguments,
            user=current_user,
            db=db,
        )
    except NodeNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except NodeVersionNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except (TimeoutError, RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))

    tool_result = {
        "tool_call_id": tool_call.id,
        "role": "tool",
        "content": json.dumps(result.get("output", {}), ensure_ascii=False),
    }
    return ApiResponse(data=tool_result)
