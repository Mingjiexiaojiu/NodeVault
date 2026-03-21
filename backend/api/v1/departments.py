import uuid

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.auth.deps import get_current_user
from backend.database.session import get_db
from backend.models.namespace import Namespace, NamespaceMember
from backend.models.node import Node
from backend.models.user import User
from backend.schemas.enums import NodeStatus
from backend.schemas.response import ApiResponse

logger = structlog.get_logger()
router = APIRouter(prefix="/departments", tags=["Departments"])


# ── schemas (local) ──────────────────────────────────────────────
from pydantic import BaseModel, Field


class DepartmentCreate(BaseModel):
    slug: str = Field(..., min_length=2, max_length=64, pattern=r"^[a-z][a-z0-9_-]{1,63}$")
    display_name: str = Field(..., min_length=1, max_length=256)
    description: str | None = None


class DepartmentUpdate(BaseModel):
    display_name: str | None = None
    description: str | None = None


class MemberAdd(BaseModel):
    username: str
    role: str = Field(default="member", pattern=r"^(admin|member)$")


# ── endpoints ────────────────────────────────────────────────────


@router.get("", response_model=ApiResponse, summary="所有部门列表")
async def list_departments(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 查询部门列表，附带成员数和节点数
    stmt = (
        select(
            Namespace,
            func.count(NamespaceMember.id.distinct()).label("member_count"),
        )
        .outerjoin(NamespaceMember, NamespaceMember.namespace_id == Namespace.id)
        .group_by(Namespace.id)
        .order_by(Namespace.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    rows = result.all()

    # 单独查节点数
    node_count_stmt = (
        select(Node.namespace_id, func.count(Node.id))
        .where(Node.status != NodeStatus.ARCHIVED.value)
        .group_by(Node.namespace_id)
    )
    nc_result = await db.execute(node_count_stmt)
    node_counts = dict(nc_result.all())

    data = []
    for ns, member_count in rows:
        data.append({
            "id": str(ns.id),
            "slug": ns.slug,
            "display_name": ns.display_name,
            "description": ns.description,
            "owner_id": str(ns.owner_id),
            "member_count": member_count,
            "node_count": node_counts.get(ns.id, 0),
            "created_at": ns.created_at.isoformat(),
        })

    total_stmt = select(func.count(Namespace.id))
    total = (await db.execute(total_stmt)).scalar() or 0

    return ApiResponse(data={"items": data, "total": total})


@router.post("", response_model=ApiResponse, status_code=status.HTTP_201_CREATED, summary="创建部门")
async def create_department(
    payload: DepartmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 仅超级管理员(0)和主管(1)可创建部门
    if current_user.role > 1:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅主管及以上身份可创建部门")

    # 检查 slug 唯一
    existing = await db.execute(select(Namespace).where(Namespace.slug == payload.slug))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="部门标识已存在")

    ns = Namespace(
        slug=payload.slug,
        display_name=payload.display_name,
        description=payload.description,
        owner_id=current_user.id,
    )
    db.add(ns)
    await db.flush()

    # 创建者自动成为管理员
    db.add(NamespaceMember(namespace_id=ns.id, user_id=current_user.id, role="admin"))
    await db.commit()
    await db.refresh(ns)

    return ApiResponse(
        data={"id": str(ns.id), "slug": ns.slug, "display_name": ns.display_name},
        message="部门已创建",
    )


@router.get("/{dept_id}", response_model=ApiResponse, summary="部门详情")
async def get_department(
    dept_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Namespace)
        .where(Namespace.id == dept_id)
        .options(selectinload(Namespace.members).selectinload(NamespaceMember.user))
    )
    ns = result.scalar_one_or_none()
    if ns is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="部门不存在")

    # 获取部门内的节点
    nodes_stmt = (
        select(Node)
        .where(Node.namespace_id == dept_id, Node.status != NodeStatus.ARCHIVED.value)
        .options(selectinload(Node.tags))
        .order_by(Node.updated_at.desc())
        .limit(100)
    )
    nodes_result = await db.execute(nodes_stmt)
    nodes = nodes_result.scalars().all()

    # 获取创建者信息
    owner_result = await db.execute(select(User).where(User.id == ns.owner_id))
    owner = owner_result.scalar_one_or_none()

    # 统计数据
    from backend.models.node import NodeInvocationLog
    node_ids = [n.id for n in nodes]
    total_invocations = 0
    if node_ids:
        inv_count = await db.execute(
            select(func.count(NodeInvocationLog.id)).where(NodeInvocationLog.node_id.in_(node_ids))
        )
        total_invocations = inv_count.scalar() or 0

    status_counts = {}
    for n in nodes:
        status_counts[n.status] = status_counts.get(n.status, 0) + 1

    type_counts = {}
    for n in nodes:
        type_counts[n.visibility] = type_counts.get(n.visibility, 0) + 1

    return ApiResponse(data={
        "id": str(ns.id),
        "slug": ns.slug,
        "display_name": ns.display_name,
        "description": ns.description,
        "owner_id": str(ns.owner_id),
        "owner_username": owner.username if owner else None,
        "created_at": ns.created_at.isoformat(),
        "stats": {
            "node_count": len(nodes),
            "member_count": len(ns.members),
            "total_invocations": total_invocations,
            "status_distribution": status_counts,
            "type_distribution": type_counts,
        },
        "members": [
            {
                "user_id": str(m.user_id),
                "username": m.user.username,
                "email": m.user.email,
                "role": m.role,
                "joined_at": m.joined_at.isoformat(),
            }
            for m in ns.members
        ],
        "nodes": [
            {
                "id": str(n.id),
                "name": n.name,
                "display_name": n.display_name,
                "type": n.visibility,
                "status": n.status,
                "tags": [t.tag for t in n.tags],
                "created_at": n.created_at.isoformat(),
            }
            for n in nodes
        ],
    })


@router.patch("/{dept_id}", response_model=ApiResponse, summary="更新部门信息")
async def update_department(
    dept_id: uuid.UUID,
    payload: DepartmentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ns = (await db.execute(select(Namespace).where(Namespace.id == dept_id))).scalar_one_or_none()
    if ns is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="部门不存在")

    # 仅管理员可修改
    membership = (await db.execute(
        select(NamespaceMember).where(
            NamespaceMember.namespace_id == dept_id,
            NamespaceMember.user_id == current_user.id,
            NamespaceMember.role == "admin",
        )
    )).scalar_one_or_none()
    if membership is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅部门管理员可修改部门信息")

    if payload.display_name is not None:
        ns.display_name = payload.display_name
    if payload.description is not None:
        ns.description = payload.description
    await db.commit()

    return ApiResponse(data={"id": str(ns.id), "display_name": ns.display_name, "description": ns.description})


@router.post("/{dept_id}/members", response_model=ApiResponse, summary="添加部门成员")
async def add_member(
    dept_id: uuid.UUID,
    payload: MemberAdd,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 验证部门存在
    ns = (await db.execute(select(Namespace).where(Namespace.id == dept_id))).scalar_one_or_none()
    if ns is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="部门不存在")

    # 仅管理员可添加成员
    admin_check = (await db.execute(
        select(NamespaceMember).where(
            NamespaceMember.namespace_id == dept_id,
            NamespaceMember.user_id == current_user.id,
            NamespaceMember.role == "admin",
        )
    )).scalar_one_or_none()
    if admin_check is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅部门管理员可添加成员")

    # 查找目标用户
    target_user = (await db.execute(
        select(User).where(User.username == payload.username)
    )).scalar_one_or_none()
    if target_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"用户 {payload.username} 不存在")

    # 检查是否已是成员
    existing = (await db.execute(
        select(NamespaceMember).where(
            NamespaceMember.namespace_id == dept_id,
            NamespaceMember.user_id == target_user.id,
        )
    )).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="该用户已是部门成员")

    db.add(NamespaceMember(namespace_id=dept_id, user_id=target_user.id, role=payload.role))
    await db.commit()

    return ApiResponse(message=f"已将 {payload.username} 添加为部门{payload.role}")


@router.delete("/{dept_id}/members/{user_id}", response_model=ApiResponse, summary="移除部门成员")
async def remove_member(
    dept_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ns = (await db.execute(select(Namespace).where(Namespace.id == dept_id))).scalar_one_or_none()
    if ns is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="部门不存在")

    # 仅管理员可操作
    admin_check = (await db.execute(
        select(NamespaceMember).where(
            NamespaceMember.namespace_id == dept_id,
            NamespaceMember.user_id == current_user.id,
            NamespaceMember.role == "admin",
        )
    )).scalar_one_or_none()
    if admin_check is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅部门管理员可移除成员")

    # 不能移除部门创建者
    if user_id == ns.owner_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不能移除部门创建者")

    membership = (await db.execute(
        select(NamespaceMember).where(
            NamespaceMember.namespace_id == dept_id,
            NamespaceMember.user_id == user_id,
        )
    )).scalar_one_or_none()
    if membership is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="该用户不是部门成员")

    await db.delete(membership)
    await db.commit()

    return ApiResponse(message="成员已移除")
