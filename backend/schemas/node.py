import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel

from backend.schemas.enums import NodeStatus, NodeVisibility
from backend.schemas.node_schema import NodeSchemaBase


class NodeCreate(NodeSchemaBase):
    """Node 注册请求体，复用 NodeSchemaBase 的全部校验规则"""
    pass


class NodeUpdate(BaseModel):
    display_name: str | None = None
    description: str | None = None
    category_id: uuid.UUID | None = None
    visibility: NodeVisibility | None = None
    status: NodeStatus | None = None


class CategoryBrief(BaseModel):
    id: uuid.UUID
    display_name: str

    model_config = {"from_attributes": True}


class NodeResponse(BaseModel):
    id: uuid.UUID
    name: str
    display_name: str | None
    description: str | None
    category_id: uuid.UUID
    category: CategoryBrief | None = None
    status: NodeStatus
    visibility: NodeVisibility
    namespace_id: uuid.UUID
    namespace_slug: str | None = None
    owner_id: uuid.UUID
    owner_username: str | None = None
    tags: list[str]
    source_credential_id: uuid.UUID | None = None
    source_path: str | None = None
    source_service_name: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class NodeVersionCreate(BaseModel):
    version: str
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    runtime_config: dict[str, Any]
    changelog: str | None = None
    is_default: bool = False


class NodeVersionUpdate(BaseModel):
    input_schema: dict[str, Any] | None = None
    output_schema: dict[str, Any] | None = None
    runtime_config: dict[str, Any] | None = None
    changelog: str | None = None


class NodeVersionResponse(BaseModel):
    id: uuid.UUID
    node_id: uuid.UUID
    version: str
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    runtime_config: dict[str, Any]
    changelog: str | None
    is_default: bool
    is_deprecated: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class NodeDetailResponse(NodeResponse):
    versions: list[NodeVersionResponse] = []
