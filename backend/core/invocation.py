"""
按 Node 名称调用的便捷函数，供 Agent 执行层（execute-tool、MCP Server）使用。
"""
from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.node import Node, NodeInvocationLog, NodeVersion
from backend.models.user import User
from backend.schemas.enums import NodeStatus
from backend.core.runtime import RuntimeDispatcher


class NodeNotFoundError(Exception):
    """没有找到匹配名称的 active Node"""


class NodeVersionNotFoundError(Exception):
    """Node 存在但没有可用的默认版本"""


async def invoke_node_by_name(
    name: str,
    arguments: dict[str, Any],
    user: User,
    db: AsyncSession,
) -> dict[str, Any]:
    """
    按 Node 名称查找并执行。

    查询条件：status=active，name 完全匹配（任意 namespace）。
    使用 is_default=True 的版本；若无则抛出 NodeVersionNotFoundError。

    返回：
        {"output": {...}, "latency_ms": int, "invocation_id": str, "version": str, "node_name": str}
    """
    # 查找 active 状态的 Node by name
    result = await db.execute(
        select(Node).where(
            Node.name == name,
            Node.status == NodeStatus.ACTIVE.value,
        )
    )
    node = result.scalar_one_or_none()
    if node is None:
        raise NodeNotFoundError(f"No active node named '{name}'")

    # 取默认版本
    ver_result = await db.execute(
        select(NodeVersion).where(
            NodeVersion.node_id == node.id,
            NodeVersion.is_default.is_(True),
        )
    )
    version = ver_result.scalar_one_or_none()
    if version is None:
        raise NodeVersionNotFoundError(
            f"Node '{name}' has no default version"
        )

    executor = RuntimeDispatcher.get_executor(version.runtime_config["type"])

    output: dict[str, Any] = {}
    latency_ms = 0
    invoke_status = "success"
    error_message: str | None = None

    try:
        output, latency_ms = await executor.execute(version.runtime_config, arguments, db=db)
    except TimeoutError as exc:
        invoke_status = "timeout"
        error_message = str(exc)
        raise
    except (RuntimeError, ValueError) as exc:
        invoke_status = "failure"
        error_message = str(exc)
        raise
    finally:
        log = NodeInvocationLog(
            node_id=node.id,
            version=version.version,
            invoked_by=user.id,
            input_data=arguments,
            output_data=output,
            status=invoke_status,
            latency_ms=latency_ms,
            error_message=error_message,
        )
        db.add(log)
        try:
            await db.execute(
                update(Node)
                .where(Node.id == node.id)
                .values(invocation_count=Node.invocation_count + 1)
            )
            await db.commit()
        except Exception:
            pass

    return {
        "node_name": node.name,
        "version": version.version,
        "output": output,
        "latency_ms": latency_ms,
        "invocation_id": str(log.id) if hasattr(log, "id") and log.id else "",
    }
