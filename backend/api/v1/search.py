import uuid as _uuid

import structlog
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.auth.deps import get_current_user
from backend.core.search import NodeSearchIndex, cleanup_stale_documents
from backend.database.session import get_db
from backend.models.category import Category
from backend.models.node import Node, NodeTag
from backend.models.user import User
from backend.schemas.enums import NodeStatus
from backend.schemas.response import ApiResponse

logger = structlog.get_logger()

router = APIRouter(prefix="/search", tags=["Search"])


# ---------------------------------------------------------------------------
# DB 回退搜索（MeiliSearch 不可用时使用）
# ---------------------------------------------------------------------------

async def _db_fallback_search(
    db: AsyncSession,
    q: str,
    category: str | None,
    tags: list[str],
    department_id: str | None,
    sort: str,
    page: int,
    page_size: int,
) -> dict:
    """当 MeiliSearch 不可用时，回退到数据库 LIKE 查询。"""
    stmt = (
        select(Node)
        .options(selectinload(Node.tags), selectinload(Node.category_rel))
        .where(Node.status == NodeStatus.ACTIVE.value)
    )
    if q:
        pattern = f"%{q}%"
        stmt = stmt.where(
            or_(
                Node.name.ilike(pattern),
                Node.display_name.ilike(pattern),
                Node.description.ilike(pattern),
            )
        )
    if category:
        stmt = stmt.join(Category, Node.category_id == Category.id).where(
            Category.display_name == category
        )
    if department_id:
        try:
            stmt = stmt.where(Node.department_id == _uuid.UUID(department_id))
        except ValueError:
            pass
    if tags:
        stmt = stmt.join(Node.tags).where(NodeTag.tag.in_(tags))

    sort_map_db = {
        "latest": Node.updated_at.desc(),
        "popular": Node.invocation_count.desc(),
    }
    if sort in sort_map_db:
        stmt = stmt.order_by(sort_map_db[sort])
    else:
        stmt = stmt.order_by(Node.updated_at.desc())

    # 总数
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    # 分页
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    nodes = list(result.scalars().unique().all())

    hits = []
    for node in nodes:
        hits.append({
            "id": str(node.id),
            "name": node.name,
            "display_name": node.display_name,
            "description": node.description,
            "category": {"id": str(node.category_id), "display_name": node.category_rel.display_name} if node.category_rel else None,
            "status": node.status,
            "department_id": str(node.department_id),
            "invocation_count": node.invocation_count,
            "tags": [t.tag for t in node.tags],
            "created_at": node.created_at.isoformat() if node.created_at else None,
            "updated_at": node.updated_at.isoformat() if node.updated_at else None,
        })

    return {"total": total, "page": page, "page_size": page_size, "results": hits}


@router.get(
    "/nodes",
    summary="全文搜索 Node",
    description="基于 MeiliSearch 对 Node 进行全文搜索，支持关键词、类型、标签、命名空间过滤及多种排序方式。MeiliSearch 不可用时自动回退到数据库搜索。",
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
    db: AsyncSession = Depends(get_db),
    background_tasks: BackgroundTasks = None,
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

    # 尝试 MeiliSearch
    meili_ok = True
    hits = []
    total = 0
    try:
        result = NodeSearchIndex().search(
            query=q,
            filters=filters,
            sort=sort_map[sort],
            page=page,
            page_size=page_size,
        )
        hits = result.get("hits", [])
        total = result.get("estimatedTotalHits", 0)
    except Exception as exc:
        logger.warning("meilisearch_search_failed_fallback_to_db", error=str(exc))
        meili_ok = False

    # MeiliSearch 失败或无结果 → 回退 DB
    if not meili_ok or (not hits and total == 0):
        data = await _db_fallback_search(db, q, category, tags, department_id, sort, page, page_size)
        if not meili_ok or data["results"]:
            return ApiResponse(data=data)

    # 交叉验证：过滤掉数据库中已不存在的节点（防止 DB 重置后索引脏数据）
    if hits:
        hit_ids = []
        for h in hits:
            try:
                hit_ids.append(_uuid.UUID(h["id"]))
            except (ValueError, KeyError):
                continue
        if hit_ids:
            existing = await db.execute(
                select(Node.id).where(Node.id.in_(hit_ids))
            )
            existing_ids = {str(row[0]) for row in existing.all()}
            fresh_hits = [h for h in hits if h.get("id") in existing_ids]
            stale_count = len(hits) - len(fresh_hits)
            if stale_count > 0:
                logger.warning("stale_search_results_filtered", stale_count=stale_count)
                total = max(0, total - stale_count)
                stale_ids = [h["id"] for h in hits if h.get("id") not in existing_ids]
                if background_tasks and stale_ids:
                    background_tasks.add_task(cleanup_stale_documents, stale_ids)
                hits = fresh_hits

    # Normalize MeiliSearch hits: convert string category to CategoryBrief object
    for h in hits:
        cat = h.get("category")
        if isinstance(cat, str):
            h["category"] = {"display_name": cat}

    return ApiResponse(data={
        "total": total,
        "page": page,
        "page_size": page_size,
        "results": hits,
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
    db: AsyncSession = Depends(get_db),
    background_tasks: BackgroundTasks = None,
):
    # 尝试 MeiliSearch
    hits = None
    try:
        result = NodeSearchIndex().search(query=q, page_size=limit)
        hits = result.get("hits", [])
    except Exception as exc:
        logger.warning("meilisearch_suggest_failed_fallback_to_db", error=str(exc))

    # MeiliSearch 失败或无结果 → 回退 DB
    if hits is None or not hits:
        pattern = f"%{q}%"
        db_result = await db.execute(
            select(Node.name, Node.display_name)
            .where(Node.status == NodeStatus.ACTIVE.value)
            .where(or_(
                Node.name.ilike(pattern),
                Node.display_name.ilike(pattern),
            ))
            .limit(limit)
        )
        db_rows = db_result.all()
        if hits is None or db_rows:
            return ApiResponse(data=[
                {"name": row[0], "display_name": row[1]}
                for row in db_rows
            ])

    # 交叉验证
    if hits:
        hit_ids = []
        for h in hits:
            try:
                hit_ids.append(_uuid.UUID(h["id"]))
            except (ValueError, KeyError):
                continue
        if hit_ids:
            existing = await db.execute(
                select(Node.id).where(Node.id.in_(hit_ids))
            )
            existing_ids = {str(row[0]) for row in existing.all()}
            fresh_hits = [h for h in hits if h.get("id") in existing_ids]
            if len(fresh_hits) < len(hits):
                stale_ids = [h["id"] for h in hits if h.get("id") not in existing_ids]
                if background_tasks and stale_ids:
                    background_tasks.add_task(cleanup_stale_documents, stale_ids)
            hits = fresh_hits

    return ApiResponse(data=[
        {"name": hit["name"], "display_name": hit.get("display_name")}
        for hit in hits
    ])


@router.post(
    "/reindex",
    summary="全量重建索引",
    description="管理员接口：将数据库中所有 active Node 批量同步到 MeiliSearch 索引。",
    responses={
        403: {"description": "非管理员无权操作"},
    },
)
async def reindex_nodes(
    current_user: User = Depends(get_current_user),
):
    if current_user.role > 1:
        raise HTTPException(status_code=403, detail="仅管理员可执行此操作")

    from backend.core.search import sync_search_index
    await sync_search_index()

    return ApiResponse(data={}, message="索引重建完成")
