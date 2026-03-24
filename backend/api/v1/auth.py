from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.deps import get_current_user
from backend.auth.jwt import create_access_token, get_password_hash, verify_password
from backend.database.session import get_db
from backend.models.api_key import ApiKey, generate_api_key
from backend.models.namespace import Namespace, NamespaceMember
from backend.models.user import User
from backend.schemas.auth import (
    ApiKeyCreate, ApiKeyCreated, ApiKeyResponse,
    TokenResponse, UserLogin, UserRegister, UserNamespaceBrief, UserResponse, ProfileUpdate,
)
from backend.schemas.response import ApiResponse

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: UserRegister, db: AsyncSession = Depends(get_db)) -> ApiResponse:
    # Check for existing email or username
    existing = await db.execute(
        select(User).where(
            (User.email == payload.email) | (User.username == payload.username)
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email or username already registered",
        )

    user = User(
        email=payload.email,
        username=payload.username,
        display_name=payload.display_name,
        hashed_password=get_password_hash(payload.password),
    )
    db.add(user)
    await db.flush()  # get user.id before creating namespace

    namespace = Namespace(
        slug=payload.username,
        display_name=payload.username,
        owner_id=user.id,
    )
    db.add(namespace)
    await db.flush()

    # 自动将创建者加为管理员成员
    db.add(NamespaceMember(namespace_id=namespace.id, user_id=user.id, role="admin"))
    await db.commit()
    await db.refresh(user)
    return ApiResponse(data=UserResponse.model_validate(user).model_dump(), message="注册成功")


@router.post("/login", response_model=ApiResponse)
async def login(payload: UserLogin, db: AsyncSession = Depends(get_db)) -> ApiResponse:
    identifier = payload.identifier
    if "@" in identifier:
        result = await db.execute(select(User).where(User.email == identifier))
    else:
        result = await db.execute(select(User).where(User.username == identifier))
    user = result.scalar_one_or_none()

    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(subject=str(user.id))
    return ApiResponse(data=TokenResponse(access_token=token).model_dump(), message="登录成功")


@router.get("/me", response_model=ApiResponse)
async def me(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> ApiResponse:
    data = UserResponse.model_validate(current_user).model_dump()
    data["role_label"] = User.ROLE_LABELS.get(current_user.role, "普通用户")
    # 查询用户的所有部门成员关系
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(NamespaceMember)
        .where(NamespaceMember.user_id == current_user.id)
        .options(selectinload(NamespaceMember.namespace))
    )
    memberships = result.scalars().all()
    data["namespaces"] = [
        UserNamespaceBrief(
            id=m.namespace.id,
            slug=m.namespace.slug,
            display_name=m.namespace.display_name,
            role=m.role,
        ).model_dump()
        for m in memberships
    ]
    return ApiResponse(data=data)


@router.patch("/profile", response_model=ApiResponse, summary="更新个人资料")
async def update_profile(
    payload: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse:
    update_data = payload.model_dump(exclude_none=True)
    for field, value in update_data.items():
        setattr(current_user, field, value)
    await db.commit()
    await db.refresh(current_user)
    data = UserResponse.model_validate(current_user).model_dump()
    data["role_label"] = User.ROLE_LABELS.get(current_user.role, "普通用户")
    return ApiResponse(data=data, message="资料已更新")


# ---- API Key 管理 -------------------------------------------------------

@router.post("/api-keys", response_model=ApiResponse, status_code=status.HTTP_201_CREATED,
             summary="创建 Agent API Key")
async def create_api_key(
    payload: ApiKeyCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse:
    """生成一个专用于 Agent 接入的 API Key。明文 key 仅本次返回，请妥善保存。"""
    full_key, key_hash = generate_api_key()
    key_prefix = full_key[:12]  # "nvk_" + 8字符
    api_key = ApiKey(
        name=payload.name,
        key_prefix=key_prefix,
        key_hash=key_hash,
        owner_id=current_user.id,
    )
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)
    return ApiResponse(
        data=ApiKeyCreated(
            id=api_key.id,
            name=api_key.name,
            key_prefix=api_key.key_prefix,
            is_active=api_key.is_active,
            created_at=api_key.created_at,
            last_used_at=api_key.last_used_at,
            full_key=full_key,
        ).model_dump(),
        message="API Key 已创建，请保存明文 key，已无法再次获取",
    )


@router.get("/api-keys", response_model=ApiResponse, summary="获取自己的 API Keys")
async def list_api_keys(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse:
    result = await db.execute(
        select(ApiKey)
        .where(ApiKey.owner_id == current_user.id)
        .order_by(ApiKey.created_at.desc())
    )
    keys = result.scalars().all()
    return ApiResponse(data=[ApiKeyResponse.model_validate(k).model_dump() for k in keys])


@router.delete("/api-keys/{key_id}", response_model=ApiResponse, summary="删除 API Key")
async def delete_api_key(
    key_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse:
    import uuid as _uuid
    try:
        kid = _uuid.UUID(key_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="无效的 key_id")
    result = await db.execute(
        select(ApiKey).where(ApiKey.id == kid, ApiKey.owner_id == current_user.id)
    )
    api_key = result.scalar_one_or_none()
    if api_key is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API Key 不存在")
    await db.delete(api_key)
    await db.commit()
    return ApiResponse(message="API Key 已删除")
