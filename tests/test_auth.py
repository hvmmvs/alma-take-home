import pytest
from httpx import AsyncClient

from tests.conftest import TEST_PASSWORD


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    resp = await client.post(
        "/api/auth/login",
        json={"username": "admin", "password": TEST_PASSWORD},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    resp = await client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "wrong"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_wrong_username(client: AsyncClient):
    resp = await client.post(
        "/api/auth/login",
        json={"username": "nobody", "password": TEST_PASSWORD},
    )
    assert resp.status_code == 401
