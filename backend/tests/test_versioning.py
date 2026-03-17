"""
Tests for versioning (tasks 5.6 + 5.7):
- VersionCompatibilityChecker unit tests
- Version management API integration tests
"""
import uuid
from unittest.mock import patch

import pytest


# ---------------------------------------------------------------------------
# VersionCompatibilityChecker unit tests (task 5.6)
# ---------------------------------------------------------------------------


def _schema(required=None, props=None) -> dict:
    return {
        "type": "object",
        "required": required or [],
        "properties": {k: {"type": v} for k, v in (props or {}).items()},
    }


def test_check_compatibility_identical_schemas():
    from backend.core.versioning import VersionCompatibilityChecker

    checker = VersionCompatibilityChecker()
    schema = _schema(required=["a"], props={"a": "string"})
    is_compat, issues = checker.check_compatibility(schema, schema)
    assert is_compat is True
    assert issues == []


def test_check_compatibility_backward_compatible_new_optional_field():
    """新增可选字段不属于 breaking change"""
    from backend.core.versioning import VersionCompatibilityChecker

    checker = VersionCompatibilityChecker()
    old = _schema(required=["a"], props={"a": "string"})
    new = _schema(required=["a"], props={"a": "string", "b": "integer"})
    is_compat, issues = checker.check_compatibility(old, new)
    assert is_compat is True
    assert issues == []


def test_check_compatibility_breaking_added_required_field():
    """新增必填字段是 breaking change"""
    from backend.core.versioning import VersionCompatibilityChecker

    checker = VersionCompatibilityChecker()
    old = _schema(required=["a"], props={"a": "string"})
    new = _schema(required=["a", "b"], props={"a": "string", "b": "integer"})
    is_compat, issues = checker.check_compatibility(old, new)
    assert is_compat is False
    assert any("BREAKING" in i for i in issues)
    assert any("b" in i for i in issues)


def test_check_compatibility_breaking_removed_field():
    """删除已有字段是 breaking change"""
    from backend.core.versioning import VersionCompatibilityChecker

    checker = VersionCompatibilityChecker()
    old = _schema(props={"a": "string", "b": "integer"})
    new = _schema(props={"a": "string"})
    is_compat, issues = checker.check_compatibility(old, new)
    assert is_compat is False
    assert any("b" in i for i in issues)


def test_check_compatibility_warning_field_type_change():
    """字段类型变更应产生警告但不算 breaking change"""
    from backend.core.versioning import VersionCompatibilityChecker

    checker = VersionCompatibilityChecker()
    old = _schema(props={"count": "integer"})
    new = _schema(props={"count": "string"})
    is_compat, issues = checker.check_compatibility(old, new)
    assert is_compat is True
    assert any("WARNING" in i for i in issues)
    assert any("count" in i for i in issues)


def test_suggest_version_bump_major():
    from backend.core.versioning import VersionCompatibilityChecker

    checker = VersionCompatibilityChecker()
    assert checker.suggest_version_bump("1.2.3", is_compatible=False) == "2.0.0"


def test_suggest_version_bump_minor():
    from backend.core.versioning import VersionCompatibilityChecker

    checker = VersionCompatibilityChecker()
    assert checker.suggest_version_bump("1.2.3", is_compatible=True, has_new_features=True) == "1.3.0"


def test_suggest_version_bump_patch():
    from backend.core.versioning import VersionCompatibilityChecker

    checker = VersionCompatibilityChecker()
    assert checker.suggest_version_bump("1.2.3", is_compatible=True, has_new_features=False) == "1.2.4"


# ---------------------------------------------------------------------------
# Version management API integration tests (task 5.7)
# ---------------------------------------------------------------------------


def _make_node_payload(unique: str) -> dict:
    return {
        "name": f"ver_node_{unique}",
        "version": "1.0.0",
        "display_name": f"Version Node {unique}",
        "description": "test node for versioning",
        "type": "tool",
        "category": "test",
        "runtime": {
            "type": "http",
            "endpoint": "https://httpbin.org/post",
            "method": "POST",
        },
        "input_schema": {"type": "object", "properties": {"x": {"type": "string"}}, "required": ["x"]},
        "output_schema": {"type": "object", "properties": {}},
    }


async def _create_node(auth_client):
    client, headers, _ = auth_client
    unique = uuid.uuid4().hex[:8]
    with patch("backend.api.v1.nodes.NodeSearchIndex"):
        resp = await client.post("/api/v1/nodes", json=_make_node_payload(unique), headers=headers)
    assert resp.status_code == 201
    return client, headers, resp.json()["id"]


@pytest.mark.anyio
async def test_create_version_returns_compatibility(auth_client):
    """创建新版本响应应包含 compatibility 字段"""
    client, headers, node_id = await _create_node(auth_client)

    new_version_payload = {
        "version": "2.0.0",
        "input_schema": {"type": "object", "properties": {"x": {"type": "string"}}, "required": ["x"]},
        "output_schema": {"type": "object", "properties": {}},
        "runtime_config": {"type": "http", "endpoint": "https://httpbin.org/post", "method": "POST"},
        "changelog": "backward compat update",
        "is_default": True,
    }

    with patch("backend.api.v1.nodes.NodeSearchIndex"):
        resp = await client.post(f"/api/v1/nodes/{node_id}/versions", json=new_version_payload, headers=headers)

    assert resp.status_code == 201
    data = resp.json()
    assert "compatibility" in data
    assert data["compatibility"]["checked"] is True
    assert "is_compatible" in data["compatibility"]
    assert "suggested_version" in data["compatibility"]


@pytest.mark.anyio
async def test_create_version_detects_breaking_change(auth_client):
    """新增必填字段时 compatibility.is_compatible 应为 False"""
    client, headers, node_id = await _create_node(auth_client)

    breaking_payload = {
        "version": "2.0.0",
        "input_schema": {
            "type": "object",
            "properties": {"x": {"type": "string"}, "new_required": {"type": "integer"}},
            "required": ["x", "new_required"],
        },
        "output_schema": {"type": "object", "properties": {}},
        "runtime_config": {"type": "http", "endpoint": "https://httpbin.org/post", "method": "POST"},
        "is_default": True,
    }

    with patch("backend.api.v1.nodes.NodeSearchIndex"):
        resp = await client.post(f"/api/v1/nodes/{node_id}/versions", json=breaking_payload, headers=headers)

    assert resp.status_code == 201
    compat = resp.json()["compatibility"]
    assert compat["is_compatible"] is False
    assert len(compat["breaking_changes"]) > 0


@pytest.mark.anyio
async def test_set_default_version(auth_client):
    """POST /{id}/versions/{ver}/set-default 应更新默认版本"""
    client, headers, node_id = await _create_node(auth_client)

    # Create v2
    with patch("backend.api.v1.nodes.NodeSearchIndex"):
        await client.post(
            f"/api/v1/nodes/{node_id}/versions",
            json={
                "version": "2.0.0",
                "input_schema": {"type": "object", "properties": {}},
                "output_schema": {"type": "object", "properties": {}},
                "runtime_config": {"type": "http", "endpoint": "https://httpbin.org/post", "method": "POST"},
                "is_default": False,
            },
            headers=headers,
        )

    resp = await client.post(
        f"/api/v1/nodes/{node_id}/versions/2.0.0/set-default", headers=headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["default_version"] == "2.0.0"


@pytest.mark.anyio
async def test_set_default_version_not_found(auth_client):
    client, headers, node_id = await _create_node(auth_client)

    resp = await client.post(
        f"/api/v1/nodes/{node_id}/versions/9.9.9/set-default", headers=headers
    )
    assert resp.status_code == 404


@pytest.mark.anyio
async def test_deprecate_non_default_version(auth_client):
    """弃用非默认版本应成功"""
    client, headers, node_id = await _create_node(auth_client)

    # Create v2 as default, then deprecate v1
    with patch("backend.api.v1.nodes.NodeSearchIndex"):
        await client.post(
            f"/api/v1/nodes/{node_id}/versions",
            json={
                "version": "2.0.0",
                "input_schema": {"type": "object", "properties": {}},
                "output_schema": {"type": "object", "properties": {}},
                "runtime_config": {"type": "http", "endpoint": "https://httpbin.org/post", "method": "POST"},
                "is_default": True,
            },
            headers=headers,
        )

    resp = await client.post(
        f"/api/v1/nodes/{node_id}/versions/1.0.0/deprecate", headers=headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "deprecated"


@pytest.mark.anyio
async def test_deprecate_default_version_rejected(auth_client):
    """不允许弃用当前默认版本，应返回 400"""
    client, headers, node_id = await _create_node(auth_client)

    # v1.0.0 is the default
    resp = await client.post(
        f"/api/v1/nodes/{node_id}/versions/1.0.0/deprecate", headers=headers
    )
    assert resp.status_code == 400


@pytest.mark.anyio
async def test_get_changelog(auth_client):
    """GET /{id}/changelog 应返回所有版本的变更记录"""
    client, headers, node_id = await _create_node(auth_client)

    # Create v2 with changelog
    with patch("backend.api.v1.nodes.NodeSearchIndex"):
        await client.post(
            f"/api/v1/nodes/{node_id}/versions",
            json={
                "version": "2.0.0",
                "input_schema": {"type": "object", "properties": {}},
                "output_schema": {"type": "object", "properties": {}},
                "runtime_config": {"type": "http", "endpoint": "https://httpbin.org/post", "method": "POST"},
                "changelog": "Added new feature",
                "is_default": True,
            },
            headers=headers,
        )

    resp = await client.get(f"/api/v1/nodes/{node_id}/changelog", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 2
    assert any(entry["version"] == "2.0.0" for entry in data)
    v2_entry = next(e for e in data if e["version"] == "2.0.0")
    assert v2_entry["changelog"] == "Added new feature"
