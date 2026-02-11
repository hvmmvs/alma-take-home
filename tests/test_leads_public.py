import io

import pytest
from httpx import AsyncClient

FAKE_PDF = b"%PDF-1.4 fake pdf content"


def _resume(name="resume.pdf", content=FAKE_PDF):
    return {"resume": (name, io.BytesIO(content), "application/pdf")}


@pytest.mark.asyncio
async def test_submit_lead(client: AsyncClient):
    resp = await client.post(
        "/api/leads",
        data={"first_name": "Jane", "last_name": "Doe", "email": "jane@example.com"},
        files=_resume(),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["first_name"] == "Jane"
    assert data["last_name"] == "Doe"
    assert data["email"] == "jane@example.com"
    assert data["state"] == "PENDING"
    assert data["resume_path"].endswith(".pdf")
    assert "id" in data


@pytest.mark.asyncio
async def test_submit_lead_without_resume_rejected(client: AsyncClient):
    resp = await client.post(
        "/api/leads",
        data={"first_name": "Jane", "last_name": "Doe", "email": "jane@example.com"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_submit_lead_invalid_email(client: AsyncClient):
    resp = await client.post(
        "/api/leads",
        data={"first_name": "Bad", "last_name": "Email", "email": "not-an-email"},
        files=_resume(),
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_submit_lead_bad_file_type(client: AsyncClient):
    resp = await client.post(
        "/api/leads",
        data={"first_name": "Jane", "last_name": "Doe", "email": "jane@example.com"},
        files={"resume": ("malware.exe", io.BytesIO(b"bad"), "application/octet-stream")},
    )
    assert resp.status_code == 400
