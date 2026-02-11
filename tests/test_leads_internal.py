import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_leads_unauthorized(client: AsyncClient):
    resp = await client.get("/api/leads")
    assert resp.status_code in (401, 403)


@pytest.mark.asyncio
async def test_list_leads(client: AsyncClient, auth_headers: dict):
    # Create a lead first
    await client.post(
        "/api/leads",
        data={"first_name": "Alice", "last_name": "Wonder", "email": "alice@example.com"},
    )
    resp = await client.get("/api/leads", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["first_name"] == "Alice"


@pytest.mark.asyncio
async def test_get_lead_by_id(client: AsyncClient, auth_headers: dict):
    create_resp = await client.post(
        "/api/leads",
        data={"first_name": "Bob", "last_name": "Builder", "email": "bob@example.com"},
    )
    lead_id = create_resp.json()["id"]

    resp = await client.get(f"/api/leads/{lead_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == lead_id


@pytest.mark.asyncio
async def test_get_lead_not_found(client: AsyncClient, auth_headers: dict):
    resp = await client.get("/api/leads/nonexistent-id", headers=auth_headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_lead_state(client: AsyncClient, auth_headers: dict):
    create_resp = await client.post(
        "/api/leads",
        data={"first_name": "Carol", "last_name": "Danvers", "email": "carol@example.com"},
    )
    lead_id = create_resp.json()["id"]

    resp = await client.patch(
        f"/api/leads/{lead_id}",
        json={"state": "REACHED_OUT"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["state"] == "REACHED_OUT"


@pytest.mark.asyncio
async def test_update_lead_state_invalid_transition(client: AsyncClient, auth_headers: dict):
    create_resp = await client.post(
        "/api/leads",
        data={"first_name": "Dave", "last_name": "Grohl", "email": "dave@example.com"},
    )
    lead_id = create_resp.json()["id"]

    # First transition: PENDING → REACHED_OUT
    await client.patch(
        f"/api/leads/{lead_id}",
        json={"state": "REACHED_OUT"},
        headers=auth_headers,
    )

    # Second transition should fail: REACHED_OUT → REACHED_OUT
    resp = await client.patch(
        f"/api/leads/{lead_id}",
        json={"state": "REACHED_OUT"},
        headers=auth_headers,
    )
    assert resp.status_code == 400
