import uuid
from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.deps import get_current_user
from backend.core.registry import NodeRegistry
from backend.database.session import get_db
from backend.models.user import User
from backend.schemas.response import ApiResponse

router = APIRouter(prefix="/nodes", tags=["Logs"])


class InvocationLogResponse(BaseModel):
    id: uuid.UUID
    node_id: uuid.UUID
    version: str | None
    invoked_by: uuid.UUID | None
    status: str
    latency_ms: int | None
    error_message: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


@router.get("/{node_id}/logs", response_model=ApiResponse)
async def list_logs(
    node_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[InvocationLogResponse]:
    registry = NodeRegistry(db)
    logs = await registry.list_logs(node_id)
    return ApiResponse(data=[InvocationLogResponse.model_validate(log).model_dump() for log in logs])
