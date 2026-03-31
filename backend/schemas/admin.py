import uuid
from datetime import datetime

from pydantic import BaseModel


# ─────────────────────────────────────────────
# User Management
# ─────────────────────────────────────────────

class AdminUserListItem(BaseModel):
    id: uuid.UUID
    email: str
    username: str
    display_name: str | None = None
    role: int
    role_label: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class AdminUserDetail(AdminUserListItem):
    avatar_url: str | None = None
    bio: str | None = None
    phone: str | None = None
    title: str | None = None
    department_count: int = 0
    node_count: int = 0
    skill_count: int = 0


class AdminUserStatusUpdate(BaseModel):
    is_active: bool


class AdminUserRoleUpdate(BaseModel):
    role: int  # 0=superadmin, 1=manager, 2=user


# ─────────────────────────────────────────────
# Global Resources
# ─────────────────────────────────────────────

class AdminNodeListItem(BaseModel):
    id: uuid.UUID
    name: str
    display_name: str | None = None
    department_id: uuid.UUID
    department_slug: str | None = None
    owner_id: uuid.UUID
    owner_username: str | None = None
    category_id: uuid.UUID
    category_name: str | None = None
    status: str
    visibility: str
    invocation_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


class AdminNodeStatusUpdate(BaseModel):
    status: str  # "active" | "disabled"


class AdminDepartmentListItem(BaseModel):
    id: uuid.UUID
    slug: str
    display_name: str | None = None
    owner_id: uuid.UUID
    owner_username: str | None = None
    supervisor_username: str | None = None
    member_count: int = 0
    node_count: int = 0
    created_at: datetime

    model_config = {"from_attributes": True}


class AdminSkillListItem(BaseModel):
    id: uuid.UUID
    name: str
    display_name: str | None = None
    owner_id: uuid.UUID
    owner_username: str | None = None
    status: str
    is_stale: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────
# Analytics
# ─────────────────────────────────────────────

class PlatformOverview(BaseModel):
    total_users: int
    total_nodes: int
    total_skills: int
    total_invocations: int
    new_users_24h: int
    invocations_24h: int


class DailyInvocationStat(BaseModel):
    date: str  # YYYY-MM-DD
    success: int
    failure: int


class TopNodeItem(BaseModel):
    id: uuid.UUID
    name: str
    display_name: str | None = None
    department_slug: str | None = None
    owner_username: str | None = None
    invocation_count: int


class TopUserItem(BaseModel):
    id: uuid.UUID
    username: str
    display_name: str | None = None
    node_count: int
    skill_count: int


# ─────────────────────────────────────────────
# System Settings
# ─────────────────────────────────────────────

ALLOWED_SETTING_KEYS = {"enable_registration", "platform_announcement", "default_user_role"}


class SystemSettingItem(BaseModel):
    key: str
    value: str | None
    updated_at: datetime

    model_config = {"from_attributes": True}


class SystemSettingUpdate(BaseModel):
    value: str


# ─────────────────────────────────────────────
# Paginated response wrapper
# ─────────────────────────────────────────────

class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int
    page_size: int


# ─────────────────────────────────────────────
# Role Application Management
# ─────────────────────────────────────────────

class AdminRoleApplicationListItem(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    username: str | None = None
    email: str | None = None
    display_name: str | None = None
    requested_role: int
    requested_role_label: str
    status: str
    reason: str | None = None
    review_note: str | None = None
    reviewed_by: uuid.UUID | None = None
    created_at: datetime
    reviewed_at: datetime | None = None

    model_config = {"from_attributes": True}
