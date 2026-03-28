import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class NodeResponse(BaseModel):
    id: uuid.UUID
    name: str
    display_name: str | None = None
    description: str | None = None
    category_id: uuid.UUID | None = None
    status: str
    visibility: str
    department_id: uuid.UUID
    owner_id: uuid.UUID
    tags: list[str] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class InvokeResponse(BaseModel):
    node_name: str
    version: str
    output: dict[str, Any]
    latency_ms: int
    invocation_id: str
