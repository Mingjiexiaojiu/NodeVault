import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.deps import get_current_user
from backend.core.registry import NodeRegistry
from backend.core.runtime import RuntimeDispatcher
from backend.database.session import get_db
from backend.models.node import Node
from backend.models.user import User
from backend.schemas.enums import NodeStatus
from backend.schemas.response import ApiResponse

router = APIRouter(prefix="/nodes", tags=["Invoke"])


class InvokeRequest(BaseModel):
    input: dict[str, Any]
    version: str | None = None


class InvokeResponse(BaseModel):
    node_name: str
    version: str
    output: dict[str, Any]
    latency_ms: int
    invocation_id: str


@router.post("/{node_id}/invoke", response_model=ApiResponse)
async def invoke_node(
    node_id: uuid.UUID,
    request: InvokeRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> InvokeResponse:
    registry = NodeRegistry(db)

    node = await registry.get_node(node_id)
    if node is None or node.status != NodeStatus.ACTIVE.value:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Node not found or not active",
        )

    node_version = await registry.get_version(node_id, request.version)
    if node_version is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Node version not found",
        )

    # Add deprecation warning header if version is deprecated
    if node_version.is_deprecated:
        response.headers["X-NodeVault-Deprecation-Warning"] = "This version is deprecated"

    executor = RuntimeDispatcher.get_executor(node_version.runtime_config["type"])

    output: dict[str, Any] = {}
    latency_ms = 0
    invoke_status = "success"
    error_message: str | None = None

    try:
        output, latency_ms = await executor.execute(
            node_version.runtime_config, request.input, db=db
        )
    except TimeoutError as exc:
        invoke_status = "timeout"
        error_message = str(exc)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))
    except (RuntimeError, ValueError) as exc:
        invoke_status = "failure"
        error_message = str(exc)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))
    finally:
        log_id = await registry.log_invocation(
            node_id=node_id,
            version=node_version.version,
            invoked_by=current_user.id,
            input_data=request.input,
            output_data=output,
            status=invoke_status,
            latency_ms=latency_ms,
            error_message=error_message,
        )
        # Increment invocation_count asynchronously; don't fail on error
        try:
            await db.execute(
                update(Node)
                .where(Node.id == node_id)
                .values(invocation_count=Node.invocation_count + 1)
            )
            await db.commit()
        except Exception:
            pass

    return ApiResponse(
        data=InvokeResponse(
            node_name=node.name,
            version=node_version.version,
            output=output,
            latency_ms=latency_ms,
            invocation_id=str(log_id),
        ).model_dump()
    )
