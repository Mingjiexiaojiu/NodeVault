import uuid
from unittest.mock import MagicMock, patch

import pytest
from httpx import AsyncClient


def _make_node_payload(unique: str, category_id: str = "") -> dict:
    return {
        "name": f"test_node_{unique}",
        "version": "1.0.0",
        "display_name": f"Test Node {unique}",
        "description": "A test node",
        "category_id": category_id,
        "runtime": {
            "type": "http",
            "endpoint": "https://httpbin.org/post",
            "method": "POST",
        },
        "input_schema": {"type": "object", "properties": {}},
        "output_schema": {"type": "object", "properties": {}},
    }


@pytest.mark.anyio
async def test_create_node_success(auth_client):
    client, headers, _ = auth_client
    unique = uuid.uuid4().hex[:8]
    resp = await client.post("/api/v1/nodes", json=_make_node_payload(unique), headers=headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == f"test_node_{unique}"
    assert "id" in data


@pytest.mark.anyio
async def test_create_node_duplicate_name(auth_client):
    client, headers, _ = auth_client
    unique = uuid.uuid4().hex[:8]
    payload = _make_node_payload(unique)
    r1 = await client.post("/api/v1/nodes", json=payload, headers=headers)
    assert r1.status_code == 201
    r2 = await client.post("/api/v1/nodes", json=payload, headers=headers)
    assert r2.status_code == 409


@pytest.mark.anyio
async def test_create_node_invalid_name(auth_client):
    client, headers, _ = auth_client
    payload = _make_node_payload("x")
    payload["name"] = "INVALID NAME"
    resp = await client.post("/api/v1/nodes", json=payload, headers=headers)
    assert resp.status_code == 422


@pytest.mark.anyio
async def test_list_nodes(auth_client):
    client, headers, _ = auth_client
    unique = uuid.uuid4().hex[:8]
    await client.post("/api/v1/nodes", json=_make_node_payload(unique), headers=headers)
    resp = await client.get("/api/v1/nodes", headers=headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.anyio
async def test_list_nodes_filter_by_category(auth_client, default_category_id):
    client, headers, _ = auth_client
    unique = uuid.uuid4().hex[:8]
    await client.post("/api/v1/nodes", json=_make_node_payload(unique, category_id=default_category_id), headers=headers)
    resp = await client.get(f"/api/v1/nodes?category_id={default_category_id}", headers=headers)
    assert resp.status_code == 200


@pytest.mark.anyio
async def test_get_node_detail(auth_client):
    client, headers, _ = auth_client
    unique = uuid.uuid4().hex[:8]
    created = await client.post("/api/v1/nodes", json=_make_node_payload(unique), headers=headers)
    node_id = created.json()["id"]
    resp = await client.get(f"/api/v1/nodes/{node_id}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == node_id


@pytest.mark.anyio
async def test_get_node_not_found(auth_client):
    client, headers, _ = auth_client
    fake_id = str(uuid.uuid4())
    resp = await client.get(f"/api/v1/nodes/{fake_id}", headers=headers)
    assert resp.status_code == 404


@pytest.mark.anyio
async def test_update_node(auth_client):
    client, headers, _ = auth_client
    unique = uuid.uuid4().hex[:8]
    created = await client.post("/api/v1/nodes", json=_make_node_payload(unique), headers=headers)
    node_id = created.json()["id"]
    resp = await client.patch(
        f"/api/v1/nodes/{node_id}",
        json={"display_name": "Updated Name"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["display_name"] == "Updated Name"


@pytest.mark.anyio
async def test_update_node_forbidden(auth_client, client: AsyncClient):
    """Another user cannot update someone else's node."""
    owner_client, owner_headers, _ = auth_client
    # Create node as owner
    unique = uuid.uuid4().hex[:8]
    created = await owner_client.post("/api/v1/nodes", json=_make_node_payload(unique), headers=owner_headers)
    node_id = created.json()["id"]

    # Register a second user
    u2 = uuid.uuid4().hex[:8]
    await client.post(
        "/api/v1/auth/register",
        json={"email": f"user2_{u2}@example.com", "username": f"user2_{u2}", "password": "Test1234!"},
    )
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": f"user2_{u2}@example.com", "password": "Test1234!"},
    )
    other_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    resp = await client.patch(f"/api/v1/nodes/{node_id}", json={"display_name": "Hacked"}, headers=other_headers)
    assert resp.status_code == 403


@pytest.mark.anyio
async def test_archive_node(auth_client):
    client, headers, _ = auth_client
    unique = uuid.uuid4().hex[:8]
    created = await client.post("/api/v1/nodes", json=_make_node_payload(unique), headers=headers)
    node_id = created.json()["id"]
    resp = await client.delete(f"/api/v1/nodes/{node_id}", headers=headers)
    assert resp.status_code == 204


@pytest.mark.anyio
async def test_list_versions(auth_client):
    client, headers, _ = auth_client
    unique = uuid.uuid4().hex[:8]
    created = await client.post("/api/v1/nodes", json=_make_node_payload(unique), headers=headers)
    node_id = created.json()["id"]
    resp = await client.get(f"/api/v1/nodes/{node_id}/versions", headers=headers)
    assert resp.status_code == 200
    versions = resp.json()
    assert len(versions) == 1
    assert versions[0]["version"] == "1.0.0"


@pytest.mark.anyio
async def test_create_version(auth_client):
    client, headers, _ = auth_client
    unique = uuid.uuid4().hex[:8]
    created = await client.post("/api/v1/nodes", json=_make_node_payload(unique), headers=headers)
    node_id = created.json()["id"]
    resp = await client.post(
        f"/api/v1/nodes/{node_id}/versions",
        json={
            "version": "2.0.0",
            "input_schema": {"type": "object", "properties": {}},
            "output_schema": {"type": "object", "properties": {}},
            "runtime_config": {"type": "http", "endpoint": "https://httpbin.org/post", "method": "POST"},
            "changelog": "Major update",
            "is_default": True,
        },
        headers=headers,
    )
    assert resp.status_code == 201
    assert resp.json()["version"] == "2.0.0"


@pytest.mark.anyio
async def test_create_duplicate_version(auth_client):
    client, headers, _ = auth_client
    unique = uuid.uuid4().hex[:8]
    created = await client.post("/api/v1/nodes", json=_make_node_payload(unique), headers=headers)
    node_id = created.json()["id"]
    version_payload = {
        "version": "1.0.0",
        "input_schema": {"type": "object", "properties": {}},
        "output_schema": {"type": "object", "properties": {}},
        "runtime_config": {"type": "http", "endpoint": "https://httpbin.org/post", "method": "POST"},
        "is_default": False,
    }
    resp = await client.post(f"/api/v1/nodes/{node_id}/versions", json=version_payload, headers=headers)
    assert resp.status_code == 409


# ---- Search index sync tests (task 4.4) ----


@pytest.mark.anyio
async def test_create_node_calls_upsert_node(auth_client):
    """创建 Node 时应调用 NodeSearchIndex.upsert_node"""
    client, headers, _ = auth_client
    unique = uuid.uuid4().hex[:8]

    with patch("backend.api.v1.nodes.NodeSearchIndex") as mock_cls:
        mock_instance = MagicMock()
        mock_cls.return_value = mock_instance

        resp = await client.post("/api/v1/nodes", json=_make_node_payload(unique), headers=headers)

    assert resp.status_code == 201
    mock_instance.upsert_node.assert_called_once()
    call_arg = mock_instance.upsert_node.call_args[0][0]
    assert call_arg["name"] == f"test_node_{unique}"


@pytest.mark.anyio
async def test_update_node_calls_upsert_node(auth_client):
    """更新 Node 时应调用 NodeSearchIndex.upsert_node"""
    client, headers, _ = auth_client
    unique = uuid.uuid4().hex[:8]
    created = await client.post("/api/v1/nodes", json=_make_node_payload(unique), headers=headers)
    node_id = created.json()["id"]

    with patch("backend.api.v1.nodes.NodeSearchIndex") as mock_cls:
        mock_instance = MagicMock()
        mock_cls.return_value = mock_instance

        resp = await client.patch(f"/api/v1/nodes/{node_id}", json={"display_name": "New Name"}, headers=headers)

    assert resp.status_code == 200
    mock_instance.upsert_node.assert_called_once()


@pytest.mark.anyio
async def test_delete_node_calls_delete_node(auth_client):
    """删除 Node 时应调用 NodeSearchIndex.delete_node"""
    client, headers, _ = auth_client
    unique = uuid.uuid4().hex[:8]
    created = await client.post("/api/v1/nodes", json=_make_node_payload(unique), headers=headers)
    node_id = created.json()["id"]

    with patch("backend.api.v1.nodes.NodeSearchIndex") as mock_cls:
        mock_instance = MagicMock()
        mock_cls.return_value = mock_instance

        resp = await client.delete(f"/api/v1/nodes/{node_id}", headers=headers)

    assert resp.status_code == 204
    mock_instance.delete_node.assert_called_once_with(node_id)


@pytest.mark.anyio
async def test_create_node_upsert_failure_does_not_break_api(auth_client):
    """NodeSearchIndex.upsert_node 异常时 API 仍返回 201"""
    client, headers, _ = auth_client
    unique = uuid.uuid4().hex[:8]

    with patch("backend.api.v1.nodes.NodeSearchIndex") as mock_cls:
        mock_instance = MagicMock()
        mock_instance.upsert_node.side_effect = RuntimeError("MeiliSearch down")
        mock_cls.return_value = mock_instance

        resp = await client.post("/api/v1/nodes", json=_make_node_payload(unique), headers=headers)

    # upsert failure is swallowed; the node is still created
    assert resp.status_code == 201
