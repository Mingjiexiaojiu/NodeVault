import structlog

from backend.core.config import settings

logger = structlog.get_logger()

_INDEX_NAME = "nodes"
_meilisearch_available = True  # 运行时标记，连接失败后设为 False


def _get_client():
    import meilisearch

    if settings.meilisearch_api_key:
        return meilisearch.Client(settings.meilisearch_url, settings.meilisearch_api_key)
    return meilisearch.Client(settings.meilisearch_url)


class NodeSearchIndex:
    """MeiliSearch 节点搜索索引管理"""

    def setup_index(self) -> None:
        """初始化搜索索引配置（同步调用，应用启动时执行）"""
        client = _get_client()
        index = client.index(_INDEX_NAME)

        index.update_searchable_attributes(
            ["name", "display_name", "description", "tags", "category", "organization_name", "team_name"]
        )
        index.update_filterable_attributes(
            ["category", "status", "department_id", "tags", "organization_name", "team_name"]
        )
        index.update_sortable_attributes(
            ["created_at", "updated_at", "invocation_count"]
        )
        index.update_ranking_rules(
            ["words", "typo", "proximity", "attribute", "sort", "exactness"]
        )

    def upsert_node(self, node_data: dict) -> None:
        """创建或更新 Node 索引文档"""
        try:
            client = _get_client()
            # MeiliSearch requires string primary key value
            doc = {**node_data, "id": str(node_data["id"])}
            client.index(_INDEX_NAME).add_documents([doc], primary_key="id")
        except Exception as exc:
            logger.warning("meilisearch_upsert_failed", node_id=str(node_data.get("id")), error=str(exc))

    def delete_node(self, node_id: str) -> None:
        """从索引中删除 Node 文档"""
        try:
            client = _get_client()
            client.index(_INDEX_NAME).delete_document(str(node_id))
        except Exception:
            logger.warning("meilisearch_delete_failed", node_id=str(node_id))

    def delete_all_documents(self) -> None:
        """清空索引中所有文档（等待任务完成）"""
        try:
            client = _get_client()
            task = client.index(_INDEX_NAME).delete_all_documents()
            client.wait_for_task(task.task_uid, timeout_in_ms=30_000)
        except Exception:
            logger.warning("meilisearch_delete_all_failed")

    def batch_upsert(self, docs: list[dict]) -> None:
        """批量写入文档并等待任务完成"""
        if not docs:
            return
        try:
            client = _get_client()
            task = client.index(_INDEX_NAME).add_documents(docs, primary_key="id")
            client.wait_for_task(task.task_uid, timeout_in_ms=60_000)
        except Exception as exc:
            logger.warning("meilisearch_batch_upsert_failed", count=len(docs), error=str(exc))

    def search(
        self,
        query: str = "",
        filters: dict | None = None,
        sort: list[str] | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        """全文搜索 Node，失败时抛出异常由调用方处理"""
        client = _get_client()
        index = client.index(_INDEX_NAME)

        filter_str = self._build_filter(filters or {})
        params: dict = {
            "offset": (page - 1) * page_size,
            "limit": page_size,
            "attributesToHighlight": ["name", "description"],
            "highlightPreTag": "<mark>",
            "highlightPostTag": "</mark>",
        }
        if filter_str:
            params["filter"] = filter_str
        if sort:
            params["sort"] = sort

        return index.search(query, params)

    def _build_filter(self, filters: dict) -> str:
        parts = []
        if filters.get("category"):
            parts.append(f'category = "{filters["category"]}"')
        if filters.get("status"):
            parts.append(f'status = "{filters["status"]}"')
        if filters.get("department_id"):
            parts.append(f'department_id = "{filters["department_id"]}"')
        if filters.get("tags"):
            tags_str = ", ".join(f'"{t}"' for t in filters["tags"])
            parts.append(f"tags IN [{tags_str}]")
        return " AND ".join(parts)


def _node_to_search_doc(node) -> dict:
    """将 Node ORM 对象转为搜索文档"""
    dept = node.department
    org_name = dept.organization.name if dept and dept.organization else None
    team_name = dept.team_name if dept else None
    return {
        "id": str(node.id),
        "name": node.name,
        "display_name": node.display_name,
        "description": node.description,
        "category": node.category_rel.display_name if node.category_rel else None,
        "status": node.status,
        "department_id": str(node.department_id),
        "organization_name": org_name,
        "team_name": team_name,
        "invocation_count": node.invocation_count,
        "tags": [t.tag for t in node.tags],
        "created_at": node.created_at.isoformat() if node.created_at else None,
        "updated_at": node.updated_at.isoformat() if node.updated_at else None,
    }


async def sync_search_index():
    """将数据库中所有存活节点同步到 MeiliSearch，清除脏数据。

    使用批量写入并等待完成，确保索引立即可用。
    """
    global _meilisearch_available
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    from backend.database.session import async_session_factory
    from backend.models.node import Node
    from backend.models.department import Department

    async with async_session_factory() as db:
        result = await db.execute(
            select(Node)
            .options(
                selectinload(Node.tags),
                selectinload(Node.category_rel),
                selectinload(Node.department).selectinload(Department.organization),
            )
            .where(Node.status != "archived")
        )
        nodes = list(result.scalars().all())

    try:
        index = NodeSearchIndex()
        index.delete_all_documents()
        docs = [_node_to_search_doc(n) for n in nodes]
        index.batch_upsert(docs)
        _meilisearch_available = True
        logger.info("search_index_synced", node_count=len(nodes))
    except Exception as exc:
        _meilisearch_available = False
        logger.warning("search_index_sync_failed", error=str(exc))


def cleanup_stale_documents(stale_ids: list[str]):
    """从 MeiliSearch 中删除指定的脏文档（轻量操作，不影响正常数据）。"""
    index = NodeSearchIndex()
    for sid in stale_ids:
        index.delete_node(sid)
