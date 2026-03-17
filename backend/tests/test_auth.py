import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_register_success(client: AsyncClient):
    unique = uuid.uuid4().hex[:8]
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"new_{unique}@example.com",
            "username": f"newuser_{unique}",
            "password": "Test1234!",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == f"new_{unique}@example.com"
    assert "hashed_password" not in data


@pytest.mark.anyio
async def test_register_duplicate_email(client: AsyncClient):
    unique = uuid.uuid4().hex[:8]
    payload = {
        "email": f"dup_{unique}@example.com",
        "username": f"dupuser_{unique}",
        "password": "Test1234!",
    }
    r1 = await client.post("/api/v1/auth/register", json=payload)
    assert r1.status_code == 201

    payload2 = {**payload, "username": f"other_{unique}"}
    r2 = await client.post("/api/v1/auth/register", json=payload2)
    assert r2.status_code == 409


@pytest.mark.anyio
async def test_register_weak_password(client: AsyncClient):
    unique = uuid.uuid4().hex[:8]
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"weak_{unique}@example.com",
            "username": f"weakuser_{unique}",
            "password": "weak",
        },
    )
    assert resp.status_code == 422


@pytest.mark.anyio
async def test_login_success(auth_client):
    client, headers, user_data = auth_client
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": user_data["email"], "password": user_data["password"]},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.anyio
async def test_login_wrong_password(auth_client):
    client, _, user_data = auth_client
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": user_data["email"], "password": "WrongPass1!"},
    )
    assert resp.status_code == 401


@pytest.mark.anyio
async def test_me_valid_token(auth_client):
    client, headers, user_data = auth_client
    resp = await client.get("/api/v1/auth/me", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["email"] == user_data["email"]


@pytest.mark.anyio
async def test_me_no_token(client: AsyncClient):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code in (401, 403)


@pytest.mark.anyio
async def test_me_invalid_token(client: AsyncClient):
    resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid.token.here"},
    )
    assert resp.status_code == 401
