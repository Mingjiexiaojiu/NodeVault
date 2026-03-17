"""
Tests for search API (tasks 2.3 + 3.4):
- NodeSearchIndex unit tests (with mock MeiliSearch client)
- Search API integration tests (with mocked NodeSearchIndex)
"""
import uuid
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# NodeSearchIndex unit tests (task 2.3)
# ---------------------------------------------------------------------------


def _make_node_doc(uid: str) -> dict:
    return {
        "id": uid,
        "name": f"node_{uid}",
        "display_name": f"Node {uid}",
        "description": "test node",
        "type": "tool",
        "status": "active",
        "namespace_id": str(uuid.uuid4()),
        "invocation_count": 0,
        "tags": ["ai", "test"],
    }


def test_upsert_node_calls_add_documents():
    """upsert_node 应调用 MeiliSearch add_documents"""
    with patch("backend.core.search._get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        from backend.core.search import NodeSearchIndex

        idx = NodeSearchIndex()
        doc = _make_node_doc(str(uuid.uuid4()))
        idx.upsert_node(doc)

        mock_client.index.assert_called_once_with("nodes")
        mock_client.index.return_value.add_documents.assert_called_once()
        args = mock_client.index.return_value.add_documents.call_args[0]
        assert args[0][0]["id"] == doc["id"]


def test_upsert_node_swallows_exception():
    """upsert_node 在 MeiliSearch 异常时不应抛出异常"""
    with patch("backend.core.search._get_client") as mock_get_client:
        mock_get_client.side_effect = Exception("connection refused")

        from backend.core.search import NodeSearchIndex

        idx = NodeSearchIndex()
        # Should not raise
        idx.upsert_node(_make_node_doc(str(uuid.uuid4())))


def test_delete_node_calls_delete_document():
    """delete_node 应调用 MeiliSearch delete_document"""
    with patch("backend.core.search._get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        from backend.core.search import NodeSearchIndex

        node_id = str(uuid.uuid4())
        NodeSearchIndex().delete_node(node_id)

        mock_client.index.return_value.delete_document.assert_called_once_with(node_id)


def test_delete_node_swallows_exception():
    """delete_node 在异常时不应抛出"""
    with patch("backend.core.search._get_client") as mock_get_client:
        mock_get_client.side_effect = RuntimeError("meilisearch down")

        from backend.core.search import NodeSearchIndex

        NodeSearchIndex().delete_node(str(uuid.uuid4()))  # should not raise


def test_search_passes_query_and_filters():
    """search 应将正确的 query/filter 参数传递给 MeiliSearch"""
    with patch("backend.core.search._get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.index.return_value.search.return_value = {"hits": [], "estimatedTotalHits": 0}
        mock_get_client.return_value = mock_client

        from backend.core.search import NodeSearchIndex

        NodeSearchIndex().search(
            query="hello",
            filters={"type": "tool", "status": "active"},
            page=1,
            page_size=10,
        )

        call_kwargs = mock_client.index.return_value.search.call_args
        assert call_kwargs[0][0] == "hello"
        params = call_kwargs[0][1]
        assert params["limit"] == 10
        assert params["offset"] == 0
        assert 'type = "tool"' in params["filter"]
        assert 'status = "active"' in params["filter"]


def test_build_filter_single_tag():
    """_build_filter 针对 tags 生成 IN 过滤"""
    from backend.core.search import NodeSearchIndex

    idx = NodeSearchIndex()
    f = idx._build_filter({"tags": ["ai", "nlp"]})
    assert "tags IN" in f
    assert '"ai"' in f
    assert '"nlp"' in f


def test_build_filter_empty():
    from backend.core.search import NodeSearchIndex

    assert NodeSearchIndex()._build_filter({}) == ""


# ---------------------------------------------------------------------------
# Search API integration tests (task 3.4)
# ---------------------------------------------------------------------------


def _make_node_payload(unique: str) -> dict:
    return {
        "name": f"search_node_{unique}",
        "version": "1.0.0",
        "display_name": f"Search Node {unique}",
        "description": "searchable node",
        "type": "tool",
        "category": "test",
        "runtime": {
            "type": "http",
            "endpoint": "https://httpbin.org/post",
            "method": "POST",
        },
        "input_schema": {"type": "object", "properties": {}},
        "output_schema": {"type": "object", "properties": {}},
    }


@pytest.mark.anyio
async def test_search_nodes_returns_results(auth_client):
    """GET /search/nodes 在 MeiliSearch 可用时返回结果"""
    client, headers, _ = auth_client

    mock_result = {
        "hits": [{"id": str(uuid.uuid4()), "name": "test", "_formatted": {}}],
        "estimatedTotalHits": 1,
    }
    with patch("backend.api.v1.search.NodeSearchIndex") as mock_cls:
        mock_cls.return_value.search.return_value = mock_result

        resp = await client.get("/api/v1/search/nodes?q=test", headers=headers)

    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert len(data["results"]) == 1


@pytest.mark.anyio
async def test_search_nodes_503_on_error(auth_client):
    """GET /search/nodes 在 MeiliSearch 不可用时返回 503"""
    client, headers, _ = auth_client

    with patch("backend.api.v1.search.NodeSearchIndex") as mock_cls:
        mock_cls.return_value.search.side_effect = Exception("connection refused")

        resp = await client.get("/api/v1/search/nodes?q=test", headers=headers)

    assert resp.status_code == 503


@pytest.mark.anyio
async def test_search_nodes_with_type_filter(auth_client):
    """GET /search/nodes 支持 type 过滤参数"""
    client, headers, _ = auth_client

    with patch("backend.api.v1.search.NodeSearchIndex") as mock_cls:
        mock_cls.return_value.search.return_value = {"hits": [], "estimatedTotalHits": 0}

        resp = await client.get("/api/v1/search/nodes?q=&type=tool", headers=headers)

    assert resp.status_code == 200
    # Verify that the search was called with type filter
    call_kwargs = mock_cls.return_value.search.call_args[1]
    assert call_kwargs["filters"].get("type") == "tool"


@pytest.mark.anyio
async def test_search_nodes_pagination(auth_client):
    """GET /search/nodes 分页参数正确传递"""
    client, headers, _ = auth_client

    with patch("backend.api.v1.search.NodeSearchIndex") as mock_cls:
        mock_cls.return_value.search.return_value = {"hits": [], "estimatedTotalHits": 0}

        resp = await client.get("/api/v1/search/nodes?page=2&page_size=5", headers=headers)

    assert resp.status_code == 200
    data = resp.json()
    assert data["page"] == 2
    assert data["page_size"] == 5
    call_kwargs = mock_cls.return_value.search.call_args[1]
    assert call_kwargs["page"] == 2
    assert call_kwargs["page_size"] == 5


@pytest.mark.anyio
async def test_suggest_nodes_returns_names(auth_client):
    """GET /search/suggest 返回名称建议列表"""
    client, headers, _ = auth_client

    mock_result = {
        "hits": [
            {"name": "my_tool", "display_name": "My Tool"},
            {"name": "my_agent", "display_name": "My Agent"},
        ],
        "estimatedTotalHits": 2,
    }
    with patch("backend.api.v1.search.NodeSearchIndex") as mock_cls:
        mock_cls.return_value.search.return_value = mock_result

        resp = await client.get("/api/v1/search/suggest?q=my", headers=headers)

    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    assert data[0]["name"] == "my_tool"


@pytest.mark.anyio
async def test_suggest_nodes_503_on_error(auth_client):
    """GET /search/suggest 在异常时返回 503"""
    client, headers, _ = auth_client

    with patch("backend.api.v1.search.NodeSearchIndex") as mock_cls:
        mock_cls.return_value.search.side_effect = RuntimeError("down")

        resp = await client.get("/api/v1/search/suggest?q=test", headers=headers)

    assert resp.status_code == 503


@pytest.mark.anyio
async def test_search_requires_auth(client):
    """未认证请求 /search/nodes 应返回 401"""
    resp = await client.get("/api/v1/search/nodes?q=test")
    assert resp.status_code == 401
