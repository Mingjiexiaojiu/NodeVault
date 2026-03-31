from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.deps import get_current_user
from backend.auth.jwt import create_access_token, get_password_hash, verify_password
from backend.database.session import get_db
from backend.models.api_key import ApiKey, generate_api_key
from backend.models.department import Department, DepartmentMember
from backend.models.role_application import RoleApplication
from backend.models.user import User
from backend.schemas.auth import (
    ApiKeyCreate, ApiKeyCreated, ApiKeyResponse,
    TokenResponse, UserLogin, UserRegister, UserDepartmentBrief, UserResponse, ProfileUpdate,
)
from backend.schemas.role_application import PendingRoleApplication
from backend.schemas.response import ApiResponse

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: UserRegister, db: AsyncSession = Depends(get_db)) -> ApiResponse:
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
        # 申请主管的账号在审批通过前不允许登录
        is_active=payload.requested_role != 1,
    )
    db.add(user)
    await db.flush()  # 获取 user.id，但不提交

    pending_app: RoleApplication | None = None

    # 申请主管：创建 pending role application
    if payload.requested_role == 1:
        pending_app = RoleApplication(
            user_id=user.id,
            requested_role=1,
            status="pending",
        )
        db.add(pending_app)

    # 普通用户选择部门：创建 pending DepartmentMember
    elif payload.department_id is not None:
        dept_result = await db.execute(
            select(Department).where(Department.id == payload.department_id)
        )
        if dept_result.scalar_one_or_none():
            db.add(DepartmentMember(
                department_id=payload.department_id,
                user_id=user.id,
                role="member",
                status="pending",
            ))

    await db.commit()
    await db.refresh(user)

    data = UserResponse.model_validate(user).model_dump()
    if pending_app:
        data["pending_role_application"] = PendingRoleApplication(
            requested_role=pending_app.requested_role,
            created_at=pending_app.created_at,
        ).model_dump()

    msg = "主管申请已提交，管理员审批通过后权限将自动升级" if payload.requested_role == 1 else "注册成功"
    return ApiResponse(data=data, message=msg)


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

    if not user.is_active:
        # 区分"待审批"和"已封禁"，给出不同的提示
        pending = (await db.execute(
            select(RoleApplication).where(
                RoleApplication.user_id == user.id,
                RoleApplication.status == "pending",
            )
        )).scalar_one_or_none()
        if pending:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="账号待审批，请等待管理员批准后再登录",
            )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账号已被禁用，请联系管理员",
        )

    token = create_access_token(subject=str(user.id))
    return ApiResponse(data=TokenResponse(access_token=token).model_dump(), message="登录成功")


@router.get("/me", response_model=ApiResponse)
async def me(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> ApiResponse:
    from sqlalchemy.orm import selectinload
    data = UserResponse.model_validate(current_user).model_dump()
    data["role_label"] = User.ROLE_LABELS.get(current_user.role, "普通用户")

    # 查询用户的正式部门成员关系
    result = await db.execute(
        select(DepartmentMember)
        .where(DepartmentMember.user_id == current_user.id, DepartmentMember.status == "active")
        .options(selectinload(DepartmentMember.department).selectinload(Department.organization))
    )
    memberships = result.scalars().all()
    data["departments"] = [
        UserDepartmentBrief(
            id=m.department.id,
            organization_name=m.department.organization.name if m.department.organization else "",
            team_name=m.department.team_name,
            role=m.role,
        ).model_dump()
        for m in memberships
    ]

    # 查询待审批的主管申请
    app_result = await db.execute(
        select(RoleApplication)
        .where(RoleApplication.user_id == current_user.id, RoleApplication.status == "pending")
        .order_by(RoleApplication.created_at.desc())
        .limit(1)
    )
    pending_app = app_result.scalar_one_or_none()
    if pending_app:
        data["pending_role_application"] = PendingRoleApplication(
            requested_role=pending_app.requested_role,
            created_at=pending_app.created_at,
        ).model_dump()

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
