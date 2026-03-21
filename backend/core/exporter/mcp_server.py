"""
NodeVault MCP Server 实现 (5.2)

使用 FastMCP 的 SSE transport，可作为子应用挂载到 FastAPI。
"""
from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from backend.core.exporter.openai_exporter import OpenAIExporter


def create_mcp_server() -> FastMCP:
    """
    构建 NodeVault MCP Server 实例。

    list_tools 和 call_tool 在每次请求时都需要访问数据库，
    但 FastMCP 的工具是同步注册的。
    此处将 DB 查询放在实际的异步工具函数中执行。
    """
    mcp = FastMCP(
        name="nodevault",
        instructions="NodeVault AI Capability Registry — access all registered AI nodes as tools",
    )

    @mcp.tool(description="List all active NodeVault nodes as tool descriptors")
    async def list_nodevault_nodes(
        tags: str = "",
        category: str = "",
    ) -> list[dict[str, Any]]:
        """返回所有 active Node 的 OpenAI tool 描述列表"""
        from backend.core.registry import NodeRegistry
        from backend.database.session import get_db
        from backend.schemas.enums import NodeStatus

        nodes_data: list[dict[str, Any]] = []
        async for db in get_db():
            registry = NodeRegistry(db)
            nodes = await registry.list_nodes(
                # 无 owner 过滤，查全局 active 节点
                owner=None,  # type: ignore[arg-type]
                status=NodeStatus.ACTIVE.value,
                page_size=200,
            )
            exporter = OpenAIExporter()
            for node in nodes:
                version = await registry.get_version(node.id)
                if version is None:
                    continue
                tag_list = [t.tag for t in (node.tags or [])]
                if tags and not any(t in tag_list for t in tags.split(",")):
                    continue
                node_category = node.category_rel.name if node.category_rel else None
                if category and node_category != category:
                    continue
                nodes_data.append(exporter.export_node(
                    {
                        "name": node.name,
                        "description": node.description,
                        "tags": tag_list,
                    },
                    {
                        "input_schema": version.input_schema,
                        "output_schema": version.output_schema,
                    },
                ))
            break
        return nodes_data

    @mcp.tool(description="Invoke a NodeVault node by name")
    async def invoke_nodevault_node(
        name: str,
        arguments_json: str = "{}",
    ) -> str:
        """通过名称执行 NodeVault Node，返回 JSON 字符串结果"""
        import json
        from backend.core.invocation import NodeNotFoundError, NodeVersionNotFoundError, invoke_node_by_name
        from backend.database.session import get_db

        try:
            arguments = json.loads(arguments_json)
        except json.JSONDecodeError as exc:
            return f"Error: invalid JSON arguments — {exc}"

        # MCP 调用时通过系统用户执行（不关联真实用户，用 None 占位）
        async for db in get_db():
            try:
                result = await invoke_node_by_name(
                    name=name,
                    arguments=arguments,
                    user=None,  # type: ignore[arg-type]
                    db=db,
                )
                return json.dumps(result.get("output", {}), ensure_ascii=False, indent=2)
            except NodeNotFoundError as exc:
                return f"Error: {exc}"
            except NodeVersionNotFoundError as exc:
                return f"Error: {exc}"
            except Exception as exc:
                return f"Error: {exc}"
        return "Error: database unavailable"

    return mcp
