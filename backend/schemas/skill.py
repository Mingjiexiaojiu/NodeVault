import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, field_validator


class SkillCreate(BaseModel):
    name: str
    display_name: str | None = None
    description: str | None = None
    department_id: uuid.UUID

    @field_validator("name")
    @classmethod
    def name_must_be_kebab(cls, v: str) -> str:
        import re
        if not re.match(r"^[a-z0-9]+(-[a-z0-9]+)*$", v):
            raise ValueError("name 必须为 kebab-case 格式（小写字母、数字和连字符）")
        if len(v) > 64:
            raise ValueError("name 长度不能超过 64 个字符")
        return v


class SkillUpdate(BaseModel):
    display_name: str | None = None
    description: str | None = None
    status: str | None = None


class SkillResponse(BaseModel):
    id: uuid.UUID
    name: str
    display_name: str | None
    description: str | None
    department_id: uuid.UUID
    owner_id: uuid.UUID
    status: str
    is_system: bool
    is_stale: bool
    node_count: int = 0
    latest_version: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SkillNodeItem(BaseModel):
    id: uuid.UUID
    name: str
    display_name: str | None
    usage_hint: str | None
    category_name: str | None = None

    model_config = {"from_attributes": True}


class SkillDetailResponse(SkillResponse):
    nodes: list[SkillNodeItem] = []
    versions: list["SkillVersionResponse"] = []


class SkillNodeCreate(BaseModel):
    node_id: uuid.UUID
    usage_hint: str | None = None


class SkillNodeUpdate(BaseModel):
    usage_hint: str | None = None


class SkillNodeRead(BaseModel):
    id: uuid.UUID
    skill_id: uuid.UUID
    node_id: uuid.UUID
    usage_hint: str | None
    sort_order: int
    node_name: str | None = None
    node_display_name: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class SkillVersionCreate(BaseModel):
    version: str
    skill_md: str
    release_notes: str | None = None
    is_default: bool = True

    @field_validator("version")
    @classmethod
    def version_semver(cls, v: str) -> str:
        import re
        if not re.match(r"^\d+\.\d+\.\d+$", v):
            raise ValueError("version 必须使用语义化版本格式，如 1.0.0")
        return v


class SkillVersionResponse(BaseModel):
    id: uuid.UUID
    skill_id: uuid.UUID
    version: str
    skill_md: str
    node_snapshot: list[dict[str, Any]]
    release_notes: str | None
    is_default: bool
    created_at: datetime

    model_config = {"from_attributes": True}
