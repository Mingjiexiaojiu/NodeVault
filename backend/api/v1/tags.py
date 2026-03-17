from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.deps import get_current_user
from backend.database.session import get_db
from backend.models.node import Node, NodeTag
from backend.models.user import User
from backend.schemas.enums import NodeStatus
from backend.schemas.node import NodeResponse
from backend.schemas.response import ApiResponse

router = APIRouter(prefix="/tags", tags=["Tags"])


@router.get(
    "",
    summary="获取热门标签",
    description="统计当前系统内各标签关联的 active Node 数量，按数量降序返回。",
)
async def list_popular_tags(
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(NodeTag.tag, func.count(NodeTag.node_id).label("node_count"))
        .join(Node, Node.id == NodeTag.node_id)
        .where(Node.status == NodeStatus.ACTIVE.value)
        .group_by(NodeTag.tag)
        .order_by(func.count(NodeTag.node_id).desc())
        .limit(limit)
    )
    rows = result.all()
    return ApiResponse(data=[{"tag": row.tag, "node_count": row.node_count} for row in rows])


@router.get(
    "/{tag}/nodes",
    summary="按标签浏览 Node",
    description="返回带有指定标签的所有 active Node 列表，支持分页。",
)
async def nodes_by_tag(
    tag: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from sqlalchemy.orm import selectinload

    result = await db.execute(
        select(Node)
        .join(NodeTag, NodeTag.node_id == Node.id)
        .where(NodeTag.tag == tag, Node.status == NodeStatus.ACTIVE.value)
        .options(selectinload(Node.tags))
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    nodes = list(result.scalars().all())

    # count
    count_result = await db.execute(
        select(func.count())
        .select_from(Node)
        .join(NodeTag, NodeTag.node_id == Node.id)
        .where(NodeTag.tag == tag, Node.status == NodeStatus.ACTIVE.value)
    )
    total = count_result.scalar_one()

    return ApiResponse(data={
        "tag": tag,
        "total": total,
        "page": page,
        "page_size": page_size,
        "nodes": [
            {
                "id": str(n.id),
                "name": n.name,
                "display_name": n.display_name,
                "description": n.description,
                "type": n.type,
                "status": n.status,
                "tags": [t.tag for t in n.tags],
            }
            for n in nodes
        ],
    })
