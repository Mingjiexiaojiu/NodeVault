import structlog

from backend.core.config import settings

logger = structlog.get_logger()

_INDEX_NAME = "nodes"


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
            ["name", "display_name", "description", "tags", "category"]
        )
        index.update_filterable_attributes(
            ["category", "status", "department_id", "tags"]
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
        except Exception:
            logger.warning("meilisearch_upsert_failed", node_id=str(node_data.get("id")))

    def delete_node(self, node_id: str) -> None:
        """从索引中删除 Node 文档"""
        try:
            client = _get_client()
            client.index(_INDEX_NAME).delete_document(str(node_id))
        except Exception:
            logger.warning("meilisearch_delete_failed", node_id=str(node_id))

    def search(
        self,
        query: str = "",
        filters: dict | None = None,
        sort: list[str] | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        """全文搜索 Node"""
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
