"""Admin API — superadmin-only endpoints.

All routes under /admin require role == 0 (superadmin).
"""

import uuid
from datetime import datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.deps import get_current_user, get_superadmin_user
from backend.database.session import get_db
from backend.models.namespace import Namespace, NamespaceMember
from backend.models.node import Node, NodeInvocationLog
from backend.models.skill import Skill
from backend.models.system_setting import SystemSetting
from backend.models.user import User
from backend.schemas.admin import (
    ALLOWED_SETTING_KEYS,
    AdminNamespaceListItem,
    AdminNodeListItem,
    AdminNodeStatusUpdate,
    AdminSkillListItem,
    AdminUserDetail,
    AdminUserListItem,
    AdminUserRoleUpdate,
    AdminUserStatusUpdate,
    DailyInvocationStat,
    PlatformOverview,
    SystemSettingItem,
    SystemSettingUpdate,
    TopNodeItem,
    TopUserItem,
)
from backend.schemas.response import ApiResponse

router = APIRouter(prefix="/admin", tags=["Admin"])

# ─────────────────────────────────────────────────────────────
# Helper: ensure the operation doesn't strand the last superadmin
# ─────────────────────────────────────────────────────────────

async def _count_superadmins(db: AsyncSession) -> int:
    result = await db.execute(select(func.count()).where(User.role == 0))
    return result.scalar_one()


def _only_superadmin_guard(msg: str) -> None:
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)


# ═══════════════════════════════════════════════════════════════
# USER MANAGEMENT
# ═══════════════════════════════════════════════════════════════

@router.get("/users", response_model=ApiResponse)
async def list_users(
    q: str | None = Query(None, description="Filter by username or email"),
    role: int | None = Query(None, description="Filter by role (0/1/2)"),
    is_active: bool | None = Query(None, description="Filter by active status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_superadmin_user),
) -> ApiResponse:
    stmt = select(User)
    if q:
        stmt = stmt.where(
            (User.username.ilike(f"%{q}%")) | (User.email.ilike(f"%{q}%"))
        )
    if role is not None:
        stmt = stmt.where(User.role == role)
    if is_active is not None:
        stmt = stmt.where(User.is_active == is_active)

    count_result = await db.execute(select(func.count()).select_from(stmt.subquery()))
    total = count_result.scalar_one()

    stmt = stmt.order_by(User.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    users = result.scalars().all()

    items = [
        AdminUserListItem(
            id=u.id,
            email=u.email,
            username=u.username,
            display_name=u.display_name,
            role=u.role,
            role_label=User.ROLE_LABELS.get(u.role, "未知"),
            is_active=u.is_active,
            created_at=u.created_at,
        )
        for u in users
    ]
    return ApiResponse(data={"items": [i.model_dump() for i in items], "total": total, "page": page, "page_size": page_size})


@router.get("/users/{user_id}", response_model=ApiResponse)
async def get_user_detail(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_superadmin_user),
) -> ApiResponse:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")

    ns_count = (await db.execute(select(func.count()).where(Namespace.owner_id == user_id))).scalar_one()
    node_count = (await db.execute(select(func.count()).where(Node.owner_id == user_id))).scalar_one()
    skill_count = (await db.execute(select(func.count()).where(Skill.owner_id == user_id))).scalar_one()

    detail = AdminUserDetail(
        id=user.id,
        email=user.email,
        username=user.username,
        display_name=user.display_name,
        role=user.role,
        role_label=User.ROLE_LABELS.get(user.role, "未知"),
        is_active=user.is_active,
        created_at=user.created_at,
        avatar_url=user.avatar_url,
        bio=user.bio,
        phone=user.phone,
        department=user.department,
        title=user.title,
        namespace_count=ns_count,
        node_count=node_count,
        skill_count=skill_count,
    )
    return ApiResponse(data=detail.model_dump())


@router.patch("/users/{user_id}/status", response_model=ApiResponse)
async def update_user_status(
    user_id: uuid.UUID,
    payload: AdminUserStatusUpdate,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_superadmin_user),
) -> ApiResponse:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")

    if not payload.is_active and user.role == 0:
        if await _count_superadmins(db) <= 1:
            _only_superadmin_guard("Cannot disable the only superadmin")

    user.is_active = payload.is_active
    await db.commit()
    return ApiResponse(data={"id": str(user_id), "is_active": payload.is_active}, message="状态已更新")


@router.patch("/users/{user_id}/role", response_model=ApiResponse)
async def update_user_role(
    user_id: uuid.UUID,
    payload: AdminUserRoleUpdate,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_superadmin_user),
) -> ApiResponse:
    if payload.role not in (0, 1, 2):
        raise HTTPException(status_code=400, detail="角色值必须为 0、1 或 2")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")

    if user.role == 0 and payload.role != 0:
        if await _count_superadmins(db) <= 1:
            _only_superadmin_guard("Cannot demote the only superadmin")

    user.role = payload.role
    await db.commit()
    return ApiResponse(data={"id": str(user_id), "role": payload.role}, message="角色已更新")


@router.delete("/users/{user_id}", response_model=ApiResponse)
async def delete_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_superadmin_user),
) -> ApiResponse:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")

    if user.role == 0:
        if await _count_superadmins(db) <= 1:
            _only_superadmin_guard("Cannot delete the only superadmin")

    await db.delete(user)
    await db.commit()
    return ApiResponse(data=None, message="用户已删除")


# ═══════════════════════════════════════════════════════════════
# GLOBAL RESOURCES
# ═══════════════════════════════════════════════════════════════

@router.get("/nodes", response_model=ApiResponse)
async def list_all_nodes(
    namespace_id: uuid.UUID | None = Query(None),
    status: str | None = Query(None),
    category_id: uuid.UUID | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_superadmin_user),
) -> ApiResponse:
    stmt = select(Node)
    if namespace_id:
        stmt = stmt.where(Node.namespace_id == namespace_id)
    if status:
        stmt = stmt.where(Node.status == status)
    if category_id:
        stmt = stmt.where(Node.category_id == category_id)

    count_result = await db.execute(select(func.count()).select_from(stmt.subquery()))
    total = count_result.scalar_one()

    stmt = stmt.order_by(Node.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    nodes = result.scalars().all()

    # gather namespace slugs and owner usernames in bulk
    ns_ids = list({n.namespace_id for n in nodes})
    owner_ids = list({n.owner_id for n in nodes})
    ns_map: dict[uuid.UUID, str] = {}
    owner_map: dict[uuid.UUID, str] = {}

    if ns_ids:
        ns_result = await db.execute(select(Namespace.id, Namespace.slug).where(Namespace.id.in_(ns_ids)))
        ns_map = {row.id: row.slug for row in ns_result}
    if owner_ids:
        u_result = await db.execute(select(User.id, User.username).where(User.id.in_(owner_ids)))
        owner_map = {row.id: row.username for row in u_result}

    items = [
        AdminNodeListItem(
            id=n.id,
            name=n.name,
            display_name=n.display_name,
            namespace_id=n.namespace_id,
            namespace_slug=ns_map.get(n.namespace_id),
            owner_id=n.owner_id,
            owner_username=owner_map.get(n.owner_id),
            category_id=n.category_id,
            status=n.status,
            visibility=n.visibility,
            invocation_count=n.invocation_count,
            created_at=n.created_at,
        )
        for n in nodes
    ]
    return ApiResponse(data={"items": [i.model_dump() for i in items], "total": total, "page": page, "page_size": page_size})


@router.patch("/nodes/{node_id}/status", response_model=ApiResponse)
async def admin_update_node_status(
    node_id: uuid.UUID,
    payload: AdminNodeStatusUpdate,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_superadmin_user),
) -> ApiResponse:
    if payload.status not in ("active", "disabled", "draft", "deprecated"):
        raise HTTPException(status_code=400, detail="无效的节点状态值")
    result = await db.execute(select(Node).where(Node.id == node_id))
    node = result.scalar_one_or_none()
    if node is None:
        raise HTTPException(status_code=404, detail="节点不存在")
    node.status = payload.status
    await db.commit()
    return ApiResponse(data={"id": str(node_id), "status": payload.status}, message="节点状态已更新")


@router.get("/namespaces", response_model=ApiResponse)
async def list_all_namespaces(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_superadmin_user),
) -> ApiResponse:
    stmt = select(Namespace).order_by(Namespace.created_at.desc())
    count_result = await db.execute(select(func.count()).select_from(stmt.subquery()))
    total = count_result.scalar_one()

    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    namespaces = result.scalars().all()

    ns_ids = [ns.id for ns in namespaces]
    owner_ids = list({ns.owner_id for ns in namespaces})
    member_map: dict[uuid.UUID, int] = {}
    node_map: dict[uuid.UUID, int] = {}
    owner_map: dict[uuid.UUID, str] = {}

    if ns_ids:
        m_result = await db.execute(
            select(NamespaceMember.namespace_id, func.count().label("cnt"))
            .where(NamespaceMember.namespace_id.in_(ns_ids))
            .group_by(NamespaceMember.namespace_id)
        )
        member_map = {row.namespace_id: row.cnt for row in m_result}

        n_result = await db.execute(
            select(Node.namespace_id, func.count().label("cnt"))
            .where(Node.namespace_id.in_(ns_ids))
            .group_by(Node.namespace_id)
        )
        node_map = {row.namespace_id: row.cnt for row in n_result}

    if owner_ids:
        u_result = await db.execute(select(User.id, User.username).where(User.id.in_(owner_ids)))
        owner_map = {row.id: row.username for row in u_result}

    items = [
        AdminNamespaceListItem(
            id=ns.id,
            slug=ns.slug,
            display_name=ns.display_name,
            owner_id=ns.owner_id,
            owner_username=owner_map.get(ns.owner_id),
            member_count=member_map.get(ns.id, 0),
            node_count=node_map.get(ns.id, 0),
            created_at=ns.created_at,
        )
        for ns in namespaces
    ]
    return ApiResponse(data={"items": [i.model_dump() for i in items], "total": total, "page": page, "page_size": page_size})


@router.get("/skills", response_model=ApiResponse)
async def list_all_skills(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_superadmin_user),
) -> ApiResponse:
    stmt = select(Skill).order_by(Skill.created_at.desc())
    count_result = await db.execute(select(func.count()).select_from(stmt.subquery()))
    total = count_result.scalar_one()

    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    skills = result.scalars().all()

    ns_ids = list({s.namespace_id for s in skills})
    owner_ids = list({s.owner_id for s in skills})
    ns_map: dict[uuid.UUID, str] = {}
    owner_map: dict[uuid.UUID, str] = {}

    if ns_ids:
        ns_result = await db.execute(select(Namespace.id, Namespace.slug).where(Namespace.id.in_(ns_ids)))
        ns_map = {row.id: row.slug for row in ns_result}
    if owner_ids:
        u_result = await db.execute(select(User.id, User.username).where(User.id.in_(owner_ids)))
        owner_map = {row.id: row.username for row in u_result}

    items = [
        AdminSkillListItem(
            id=s.id,
            name=s.name,
            display_name=s.display_name,
            namespace_id=s.namespace_id,
            namespace_slug=ns_map.get(s.namespace_id),
            owner_id=s.owner_id,
            owner_username=owner_map.get(s.owner_id),
            status=s.status,
            is_stale=s.is_stale,
            created_at=s.created_at,
        )
        for s in skills
    ]
    return ApiResponse(data={"items": [i.model_dump() for i in items], "total": total, "page": page, "page_size": page_size})


# ═══════════════════════════════════════════════════════════════
# PLATFORM ANALYTICS
# ═══════════════════════════════════════════════════════════════

@router.get("/analytics/overview", response_model=ApiResponse)
async def analytics_overview(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_superadmin_user),
) -> ApiResponse:
    now = datetime.utcnow()
    since_24h = now - timedelta(hours=24)

    total_users = (await db.execute(select(func.count()).select_from(User))).scalar_one()
    total_nodes = (await db.execute(select(func.count()).select_from(Node))).scalar_one()
    total_skills = (await db.execute(select(func.count()).select_from(Skill))).scalar_one()
    total_invocations = (await db.execute(select(func.count()).select_from(NodeInvocationLog))).scalar_one()
    new_users_24h = (await db.execute(
        select(func.count()).where(User.created_at >= since_24h)
    )).scalar_one()
    invocations_24h = (await db.execute(
        select(func.count()).where(NodeInvocationLog.created_at >= since_24h)
    )).scalar_one()

    overview = PlatformOverview(
        total_users=total_users,
        total_nodes=total_nodes,
        total_skills=total_skills,
        total_invocations=total_invocations,
        new_users_24h=new_users_24h,
        invocations_24h=invocations_24h,
    )
    return ApiResponse(data=overview.model_dump())


@router.get("/analytics/invocations", response_model=ApiResponse)
async def analytics_invocations(
    range: str = Query("30d", pattern=r"^(7d|30d|90d)$"),
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_superadmin_user),
) -> ApiResponse:
    days_map = {"7d": 7, "30d": 30, "90d": 90}
    days = days_map[range]
    since = datetime.utcnow() - timedelta(days=days)

    result = await db.execute(
        select(
            func.date(NodeInvocationLog.created_at).label("date"),
            func.sum(
                func.cast(NodeInvocationLog.status == "success", type_=None)
            ).label("success"),
            func.sum(
                func.cast(NodeInvocationLog.status != "success", type_=None)
            ).label("failure"),
        )
        .where(NodeInvocationLog.created_at >= since)
        .group_by(func.date(NodeInvocationLog.created_at))
        .order_by(func.date(NodeInvocationLog.created_at))
    )
    rows = result.all()
    stats = [
        DailyInvocationStat(
            date=str(row.date),
            success=int(row.success or 0),
            failure=int(row.failure or 0),
        )
        for row in rows
    ]
    return ApiResponse(data=[s.model_dump() for s in stats])


@router.get("/analytics/top-nodes", response_model=ApiResponse)
async def analytics_top_nodes(
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_superadmin_user),
) -> ApiResponse:
    result = await db.execute(
        select(Node).order_by(Node.invocation_count.desc()).limit(limit)
    )
    nodes = result.scalars().all()

    ns_ids = list({n.namespace_id for n in nodes})
    owner_ids = list({n.owner_id for n in nodes})
    ns_map: dict[uuid.UUID, str] = {}
    owner_map: dict[uuid.UUID, str] = {}
    if ns_ids:
        ns_result = await db.execute(select(Namespace.id, Namespace.slug).where(Namespace.id.in_(ns_ids)))
        ns_map = {row.id: row.slug for row in ns_result}
    if owner_ids:
        u_result = await db.execute(select(User.id, User.username).where(User.id.in_(owner_ids)))
        owner_map = {row.id: row.username for row in u_result}

    items = [
        TopNodeItem(
            id=n.id,
            name=n.name,
            display_name=n.display_name,
            namespace_slug=ns_map.get(n.namespace_id),
            owner_username=owner_map.get(n.owner_id),
            invocation_count=n.invocation_count,
        )
        for n in nodes
    ]
    return ApiResponse(data=[i.model_dump() for i in items])


@router.get("/analytics/top-users", response_model=ApiResponse)
async def analytics_top_users(
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_superadmin_user),
) -> ApiResponse:
    node_counts_sq = (
        select(Node.owner_id, func.count().label("node_count"))
        .group_by(Node.owner_id)
        .subquery()
    )
    skill_counts_sq = (
        select(Skill.owner_id, func.count().label("skill_count"))
        .group_by(Skill.owner_id)
        .subquery()
    )

    result = await db.execute(
        select(
            User.id,
            User.username,
            User.display_name,
            func.coalesce(node_counts_sq.c.node_count, 0).label("node_count"),
            func.coalesce(skill_counts_sq.c.skill_count, 0).label("skill_count"),
        )
        .outerjoin(node_counts_sq, User.id == node_counts_sq.c.owner_id)
        .outerjoin(skill_counts_sq, User.id == skill_counts_sq.c.owner_id)
        .order_by(func.coalesce(node_counts_sq.c.node_count, 0).desc())
        .limit(limit)
    )
    rows = result.all()
    items = [
        TopUserItem(
            id=row.id,
            username=row.username,
            display_name=row.display_name,
            node_count=row.node_count,
            skill_count=row.skill_count,
        )
        for row in rows
    ]
    return ApiResponse(data=[i.model_dump() for i in items])


# ═══════════════════════════════════════════════════════════════
# SYSTEM SETTINGS
# ═══════════════════════════════════════════════════════════════

@router.get("/settings", response_model=ApiResponse)
async def get_settings(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_superadmin_user),
) -> ApiResponse:
    result = await db.execute(select(SystemSetting).order_by(SystemSetting.key))
    settings = result.scalars().all()
    return ApiResponse(data=[SystemSettingItem.model_validate(s).model_dump() for s in settings])


@router.put("/settings/{key}", response_model=ApiResponse)
async def update_setting(
    key: str,
    payload: SystemSettingUpdate,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_superadmin_user),
) -> ApiResponse:
    if key not in ALLOWED_SETTING_KEYS:
        raise HTTPException(status_code=400, detail=f"Unknown setting key: {key}")

    result = await db.execute(select(SystemSetting).where(SystemSetting.key == key))
    setting = result.scalar_one_or_none()
    if setting is None:
        setting = SystemSetting(key=key, value=payload.value)
        db.add(setting)
    else:
        setting.value = payload.value
        setting.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(setting)
    return ApiResponse(data=SystemSettingItem.model_validate(setting).model_dump(), message="设置已保存")


# ═══════════════════════════════════════════════════════════════
# PUBLIC ANNOUNCEMENT (no auth required — registered separately)
# ═══════════════════════════════════════════════════════════════

announcement_router = APIRouter(prefix="/settings", tags=["Settings"])


@announcement_router.get("/announcement")
async def get_announcement(db: AsyncSession = Depends(get_db)) -> dict:
    result = await db.execute(
        select(SystemSetting).where(SystemSetting.key == "platform_announcement")
    )
    setting = result.scalar_one_or_none()
    return {"announcement": setting.value if setting else ""}
