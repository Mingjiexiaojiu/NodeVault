import re
import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

PASSWORD_PATTERN = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$")


class UserRegister(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=8, max_length=64, pattern=r"^[a-zA-Z0-9_][a-zA-Z0-9_-]{7,63}$")
    display_name: str = Field(..., min_length=1, max_length=128)
    password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not PASSWORD_PATTERN.match(v):
            raise ValueError(
                "Password must be at least 8 characters and contain uppercase, lowercase, and a digit"
            )
        return v


class UserLogin(BaseModel):
    identifier: str  # 邮箱或用户名
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserNamespaceBrief(BaseModel):
    id: uuid.UUID
    slug: str
    display_name: str | None = None
    role: str


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    username: str
    is_active: bool
    role: int = 2
    role_label: str = "普通用户"
    display_name: str | None = None
    avatar_url: str | None = None
    bio: str | None = None
    phone: str | None = None
    department: str | None = None
    title: str | None = None
    namespaces: list[UserNamespaceBrief] = []
    created_at: datetime

    model_config = {"from_attributes": True}


class ProfileUpdate(BaseModel):
    display_name: str | None = None
    avatar_url: str | None = None
    bio: str | None = None
    phone: str | None = None
    department: str | None = None
    title: str | None = None


class ApiKeyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=128, description="API Key 名称，便于识别")


class ApiKeyResponse(BaseModel):
    id: uuid.UUID
    name: str
    key_prefix: str
    is_active: bool
    created_at: datetime
    last_used_at: datetime | None = None

    model_config = {"from_attributes": True}


class ApiKeyCreated(ApiKeyResponse):
    """仅在创建时返回一次，包含明文 key"""
    full_key: str
