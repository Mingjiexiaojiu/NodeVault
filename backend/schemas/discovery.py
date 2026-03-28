"""Pydantic schemas for service discovery and batch import."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from backend.schemas.enums import ProbeErrorType


# ---------- Probe ----------


class ProbeRequest(BaseModel):
    base_url: str = Field(..., min_length=1, max_length=2048)
    probe_paths: list[str] | None = None


class ProbeAuthConfig(BaseModel):
    base_url: str = Field(..., min_length=1, max_length=2048)
    login_endpoint: str
    login_method: str = "POST"
    login_body: dict[str, Any]
    token_json_path: str | None = None
    probe_paths: list[str] | None = None


class ProbeAttemptSchema(BaseModel):
    path: str
    status: int | None = None
    success: bool = False
    error: str | None = None


class ProbeResultSchema(BaseModel):
    base_url: str
    found: bool = False
    spec_url: str | None = None
    needs_auth: bool = False
    error: str | None = None
    error_type: ProbeErrorType | None = None
    attempts: list[ProbeAttemptSchema] = []


# ---------- NodeDraft ----------


class NodeDraftSchema(BaseModel):
    suggested_name: str
    display_name: str
    description: str = ""
    endpoint: str
    method: str
    input_schema: dict[str, Any] = {}
    output_schema: dict[str, Any] = {}
    category: str | None = None
    tags: list[str] = []
    selected: bool = True


class NodeDraftListResponse(BaseModel):
    base_url: str
    drafts: list[NodeDraftSchema]


# ---------- Batch Import ----------


class BatchImportItem(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    display_name: str | None = None
    description: str | None = None
    endpoint: str
    method: str
    input_schema: dict[str, Any] = {}
    output_schema: dict[str, Any] = {}
    category_id: uuid.UUID | None = None
    tags: list[str] = []
    source_path: str | None = None


class BatchImportRequest(BaseModel):
    department_id: uuid.UUID
    credential_id: uuid.UUID | None = None
    base_url: str  # used to build full endpoint = base_url + item.endpoint
    items: list[BatchImportItem] = Field(..., min_length=1)
    # Public fields applied to all imported Nodes
    visibility: str = "internal"
    session_id: uuid.UUID | None = None


class BatchImportResultItem(BaseModel):
    name: str
    node_id: uuid.UUID


class BatchImportResponse(BaseModel):
    imported: int
    nodes: list[BatchImportResultItem]


# ---------- Discovery Session ----------


class DiscoverySessionCreate(BaseModel):
    base_url: str = ""
    source: str = "probe"  # "probe" | "upload"


class DiscoverySessionUpdate(BaseModel):
    status: str | None = None
    spec_url: str | None = None
    total_operations: int | None = None
    imported_count: int | None = None
    completed_at: datetime | None = None


class LinkedNodeSchema(BaseModel):
    id: uuid.UUID
    name: str
    display_name: str | None
    source_path: str | None
    status: str

    class Config:
        from_attributes = True


class DiscoverySessionSchema(BaseModel):
    id: uuid.UUID
    base_url: str
    source: str
    status: str
    spec_url: str | None
    total_operations: int | None
    imported_count: int
    created_at: datetime
    completed_at: datetime | None

    class Config:
        from_attributes = True


class DiscoverySessionDetail(DiscoverySessionSchema):
    nodes: list[LinkedNodeSchema] = []


# ---------- Iteration / Compare ----------


class CompareRequest(BaseModel):
    previous_session_id: uuid.UUID


class CompareResultItem(BaseModel):
    path: str
    method: str
    status: str  # "new" | "imported" | "updated" | "removed"
    changes: dict[str, str] | None = None


class CompareResponse(BaseModel):
    items: list[CompareResultItem]


class IterateActionItem(BaseModel):
    path: str
    method: str
    action: str  # "import" | "update" | "skip"


class IterateRequest(BaseModel):
    actions: list[IterateActionItem] = Field(..., min_length=1)


class IterateResponse(BaseModel):
    imported: int
    updated: int
    skipped: int


class DuplicateUrlResponse(BaseModel):
    duplicate: bool
    existing_session_id: uuid.UUID | None = None
    existing_count: int = 0
    message: str = ""
