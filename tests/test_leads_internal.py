import io

import pytest
from httpx import AsyncClient

FAKE_PDF = b"%PDF-1.4 fake pdf content"


def _resume():
    return {"resume": ("resume.pdf", io.BytesIO(FAKE_PDF), "application/pdf")}


async def _create_lead(client, first_name="Alice", last_name="Wonder", email="alice@example.com"):
    resp = await client.post(
        "/api/leads",
        data={"first_name": first_name, "last_name": last_name, "email": email},
        files=_resume(),
    )
    assert resp.status_code == 201
    return resp.json()


@pytest.mark.asyncio
async def test_list_leads_unauthorized(client: AsyncClient):
    resp = await client.get("/api/leads")
    assert resp.status_code in (401, 403)


@pytest.mark.asyncio
async def test_list_leads(client: AsyncClient, auth_headers: dict):
    await _create_lead(client)
    resp = await client.get("/api/leads", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["first_name"] == "Alice"


@pytest.mark.asyncio
async def test_get_lead_by_id(client: AsyncClient, auth_headers: dict):
    lead = await _create_lead(client, "Bob", "Builder", "bob@example.com")
    resp = await client.get(f"/api/leads/{lead['id']}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == lead["id"]


@pytest.mark.asyncio
async def test_get_lead_not_found(client: AsyncClient, auth_headers: dict):
    resp = await client.get("/api/leads/nonexistent-id", headers=auth_headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_lead_state(client: AsyncClient, auth_headers: dict):
    lead = await _create_lead(client, "Carol", "Danvers", "carol@example.com")
    resp = await client.patch(
        f"/api/leads/{lead['id']}",
        json={"state": "REACHED_OUT"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["state"] == "REACHED_OUT"


@pytest.mark.asyncio
async def test_update_lead_state_invalid_transition(client: AsyncClient, auth_headers: dict):
    lead = await _create_lead(client, "Dave", "Grohl", "dave@example.com")

    # First transition: PENDING → REACHED_OUT
    await client.patch(
        f"/api/leads/{lead['id']}",
        json={"state": "REACHED_OUT"},
        headers=auth_headers,
    )

    # Second transition should fail: REACHED_OUT → REACHED_OUT
    resp = await client.patch(
        f"/api/leads/{lead['id']}",
        json={"state": "REACHED_OUT"},
        headers=auth_headers,
    )
    assert resp.status_code == 400
