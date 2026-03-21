"""
导出 API：单节点和批量导出为 OpenAI / LangChain / MCP / Skill Package 格式 (3.1–3.6)
"""
from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import PlainTextResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.deps import get_current_user
from backend.core.exporter import LangChainExporter, OpenAIExporter, SkillPackageExporter
from backend.core.registry import NodeRegistry
from backend.database.session import get_db
from backend.models.node import Node, NodeVersion
from backend.models.user import User
from backend.schemas.response import ApiResponse

router = APIRouter(tags=["Export"])


# ---- helpers ----------------------------------------------------------------

def _node_to_dict(node: Node) -> dict[str, Any]:
    return {
        "id": str(node.id),
        "name": node.name,
        "display_name": node.display_name,
        "description": node.description,
        "category": node.category_rel.display_name if node.category_rel else None,
        "tags": [t.tag for t in (node.tags or [])],
    }


def _version_to_dict(version: NodeVersion) -> dict[str, Any]:
    return {
        "version": version.version,
        "input_schema": version.input_schema,
        "output_schema": version.output_schema,
    }


async def _get_node_and_version(
    node_id: uuid.UUID,
    db: AsyncSession,
) -> tuple[Node, NodeVersion]:
    registry = NodeRegistry(db)
    node = await registry.get_node(node_id)
    if node is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Node not found")
    version = await registry.get_version(node_id)
    if version is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active version available for export",
        )
    return node, version


# ---- single-node exports ----------------------------------------------------

@router.get("/nodes/{node_id}/export/openai", response_model=ApiResponse)
async def export_openai(
    node_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse:
    """导出为 OpenAI Function Calling 格式"""
    node, version = await _get_node_and_version(node_id, db)
    exporter = OpenAIExporter()
    result = exporter.export_node(_node_to_dict(node), _version_to_dict(version))
    return ApiResponse(data=result)


@router.get("/nodes/{node_id}/export/langchain", response_class=PlainTextResponse)
async def export_langchain(
    node_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PlainTextResponse:
    """导出为 LangChain StructuredTool Python 代码"""
    node, version = await _get_node_and_version(node_id, db)
    exporter = LangChainExporter()
    code = exporter.export_node(_node_to_dict(node), _version_to_dict(version))
    return PlainTextResponse(content=code, media_type="text/plain")


@router.get("/nodes/{node_id}/export/mcp", response_model=ApiResponse)
async def export_mcp(
    node_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse:
    """导出为 MCP Tool 格式"""
    node, version = await _get_node_and_version(node_id, db)
    nd = _node_to_dict(node)
    vd = _version_to_dict(version)
    from backend.core.exporter.openai_exporter import OpenAIExporter as _OE
    safe_name = _OE()._safe_name(nd["name"])
    result = {
        "name": safe_name,
        "description": nd.get("description") or "",
        "inputSchema": vd["input_schema"],
    }
    return ApiResponse(data=result)


@router.get("/nodes/{node_id}/export/skill")
async def export_skill_package(
    node_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    """下载 Skill Package ZIP"""
    node, version = await _get_node_and_version(node_id, db)
    exporter = SkillPackageExporter()
    zip_bytes = exporter.export_node(_node_to_dict(node), _version_to_dict(version))

    import io
    return StreamingResponse(
        io.BytesIO(zip_bytes),
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{node.name}.zip"',
        },
    )


# ---- batch export -----------------------------------------------------------

@router.get("/export/batch", response_model=ApiResponse)
async def batch_export(
    ids: str = Query(..., description="逗号分隔的 Node ID 列表"),
    format: str = Query("openai", enum=["openai", "langchain", "mcp"]),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse:
    """批量导出多个 Node（仅文本格式；ZIP 请逐个下载）"""
    registry = NodeRegistry(db)
    id_list: list[uuid.UUID] = []
    for raw_id in ids.split(","):
        raw_id = raw_id.strip()
        try:
            id_list.append(uuid.UUID(raw_id))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid UUID: {raw_id}",
            )

    items: list[dict[str, Any]] = []
    for nid in id_list:
        node = await registry.get_node(nid)
        if node is None:
            continue
        version = await registry.get_version(nid)
        if version is None:
            continue
        items.append({"node": _node_to_dict(node), "version": _version_to_dict(version)})

    if not items:
        return ApiResponse(data={"tools": []} if format in ("openai", "mcp") else {"code": ""})

    if format == "openai":
        exporter = OpenAIExporter()
        return ApiResponse(data={"tools": exporter.export_nodes(items)})
    elif format == "langchain":
        exporter = LangChainExporter()
        return ApiResponse(data={"code": exporter.export_nodes(items)})
    else:  # mcp
        from backend.core.exporter.openai_exporter import OpenAIExporter as _OE
        _oe = _OE()
        mcp_tools = [
            {
                "name": _oe._safe_name(item["node"]["name"]),
                "description": item["node"].get("description") or "",
                "inputSchema": item["version"]["input_schema"],
            }
            for item in items
        ]
        return ApiResponse(data={"tools": mcp_tools})
