from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.auth.deps import get_current_user
from backend.core.search import NodeSearchIndex
from backend.database.session import get_db
from backend.models.node import Node
from backend.models.user import User
from backend.schemas.enums import NodeStatus
from backend.schemas.response import ApiResponse

router = APIRouter(prefix="/search", tags=["Search"])


@router.get(
    "/nodes",
    summary="全文搜索 Node",
    description="基于 MeiliSearch 对 Node 进行全文搜索，支持关键词、类型、标签、命名空间过滤及多种排序方式。",
    responses={
        503: {"description": "搜索服务暂不可用"},
    },
)
async def search_nodes(
    q: str = Query("", description="搜索关键词，支持中英文"),
    category: str | None = Query(None),
    tags: list[str] = Query([]),
    department_id: str | None = Query(None),
    sort: str = Query("relevance", enum=["relevance", "latest", "popular"]),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
):
    sort_map = {
        "relevance": None,
        "latest": ["updated_at:desc"],
        "popular": ["invocation_count:desc"],
    }
    filters: dict = {"status": NodeStatus.ACTIVE.value}
    if category:
        filters["category"] = category
    if tags:
        filters["tags"] = tags
    if department_id:
        filters["department_id"] = department_id

    try:
        result = NodeSearchIndex().search(
            query=q,
            filters=filters,
            sort=sort_map[sort],
            page=page,
            page_size=page_size,
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Search service unavailable",
        )

    return ApiResponse(data={
        "total": result.get("estimatedTotalHits", 0),
        "page": page,
        "page_size": page_size,
        "results": result.get("hits", []),
    })


@router.get(
    "/suggest",
    summary="搜索自动补全",
    description="根据输入前缀返回 Node 名称建议，用于搜索框实时提示。",
)
async def suggest_nodes(
    q: str = Query(..., min_length=1, description="搜索词前缀"),
    limit: int = Query(5, ge=1, le=10),
    current_user: User = Depends(get_current_user),
):
    try:
        result = NodeSearchIndex().search(query=q, page_size=limit)
        return ApiResponse(data=[
            {"name": hit["name"], "display_name": hit.get("display_name")}
            for hit in result.get("hits", [])
        ])
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Search service unavailable",
        )


@router.post(
    "/reindex",
    summary="全量重建索引",
    description="管理员接口：将数据库中所有 active Node 批量同步到 MeiliSearch 索引。",
    responses={
        403: {"description": "非管理员无权操作"},
    },
)
async def reindex_nodes(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Node).options(selectinload(Node.tags), selectinload(Node.category_rel))
        .where(Node.status != "archived")
    )
    nodes = list(result.scalars().all())

    index = NodeSearchIndex()
    for node in nodes:
        index.upsert_node(
            {
                "id": str(node.id),
                "name": node.name,
                "display_name": node.display_name,
                "description": node.description,
                "category": node.category_rel.display_name if node.category_rel else None,
                "status": node.status,
                "department_id": str(node.department_id),
                "invocation_count": node.invocation_count,
                "tags": [t.tag for t in node.tags],
                "created_at": node.created_at.isoformat() if node.created_at else None,
                "updated_at": node.updated_at.isoformat() if node.updated_at else None,
            }
        )

    return ApiResponse(data={"synced": len(nodes)}, message="索引重建完成")
