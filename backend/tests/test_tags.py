"""
Tests for tags API (task 6.4):
- GET /tags returns popular tags with node_count
- GET /tags/{tag}/nodes returns paginated node list
"""
import uuid
from unittest.mock import patch

import pytest


def _make_node_payload(unique: str, category_id: str = "", tags: list | None = None) -> dict:
    payload = {
        "name": f"tag_node_{unique}",
        "version": "1.0.0",
        "display_name": f"Tag Node {unique}",
        "description": "test node for tags",
        "category_id": category_id,
        "status": "active",
        "runtime": {
            "type": "http",
            "endpoint": "https://httpbin.org/post",
            "method": "POST",
        },
        "input_schema": {"type": "object", "properties": {}},
        "output_schema": {"type": "object", "properties": {}},
    }
    if tags:
        payload["tags"] = tags
    return payload


async def _create_tagged_node(auth_client, tags: list[str]) -> str:
    client, headers, _ = auth_client
    unique = uuid.uuid4().hex[:8]
    with patch("backend.api.v1.nodes.NodeSearchIndex"):
        resp = await client.post(
            "/api/v1/nodes",
            json=_make_node_payload(unique, tags=tags),
            headers=headers,
        )
    assert resp.status_code == 201
    return resp.json()["id"]


@pytest.mark.anyio
async def test_list_popular_tags_empty(auth_client):
    """无 Node 时 /tags 返回空列表或列表（不报错）"""
    client, headers, _ = auth_client
    resp = await client.get("/api/v1/tags", headers=headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.anyio
async def test_list_popular_tags_with_nodes(auth_client):
    """创建带标签的 Node 后 /tags 应包含该标签"""
    client, headers, _ = auth_client
    tag = f"pytest_{uuid.uuid4().hex[:6]}"
    await _create_tagged_node(auth_client, tags=[tag, "shared_tag"])
    await _create_tagged_node(auth_client, tags=[tag])

    resp = await client.get("/api/v1/tags", headers=headers)
    assert resp.status_code == 200
    tags_data = resp.json()
    tag_names = [t["tag"] for t in tags_data]
    assert tag in tag_names

    # The newly created tag should have node_count >= 2
    our_tag = next(t for t in tags_data if t["tag"] == tag)
    assert our_tag["node_count"] >= 2


@pytest.mark.anyio
async def test_list_popular_tags_sorted_by_count(auth_client):
    """热门标签应按 node_count 降序排列"""
    resp = await (auth_client[0]).get("/api/v1/tags", headers=auth_client[1])
    assert resp.status_code == 200
    tags_data = resp.json()
    counts = [t["node_count"] for t in tags_data]
    assert counts == sorted(counts, reverse=True)


@pytest.mark.anyio
async def test_nodes_by_tag_returns_nodes(auth_client):
    """GET /tags/{tag}/nodes 应返回带该标签的 Node 列表"""
    client, headers, _ = auth_client
    tag = f"unique_{uuid.uuid4().hex[:6]}"
    node_id = await _create_tagged_node(auth_client, tags=[tag])

    resp = await client.get(f"/api/v1/tags/{tag}/nodes", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["tag"] == tag
    assert data["total"] >= 1
    node_ids = [n["id"] for n in data["nodes"]]
    assert node_id in node_ids


@pytest.mark.anyio
async def test_nodes_by_unknown_tag_returns_empty(auth_client):
    """不存在的 tag 应返回空列表而非 404"""
    client, headers, _ = auth_client
    resp = await client.get(f"/api/v1/tags/nonexistent_tag_xyz/nodes", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0
    assert data["nodes"] == []


@pytest.mark.anyio
async def test_nodes_by_tag_pagination(auth_client):
    """分页参数 page/page_size 应正确传递"""
    client, headers, _ = auth_client
    tag = f"paged_{uuid.uuid4().hex[:6]}"
    # Create 3 nodes with same tag
    for _ in range(3):
        await _create_tagged_node(auth_client, tags=[tag])

    resp = await client.get(f"/api/v1/tags/{tag}/nodes?page=1&page_size=2", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["nodes"]) <= 2
    assert data["page"] == 1
    assert data["page_size"] == 2
    assert data["total"] >= 3


@pytest.mark.anyio
async def test_tags_requires_auth(client):
    """未认证请求 /tags 应返回 401"""
    resp = await client.get("/api/v1/tags")
    assert resp.status_code == 401
