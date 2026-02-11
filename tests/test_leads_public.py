import io

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_submit_lead_without_resume(client: AsyncClient):
    resp = await client.post(
        "/api/leads",
        data={"first_name": "Jane", "last_name": "Doe", "email": "jane@example.com"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["first_name"] == "Jane"
    assert data["last_name"] == "Doe"
    assert data["email"] == "jane@example.com"
    assert data["state"] == "PENDING"
    assert data["resume_path"] is None
    assert "id" in data


@pytest.mark.asyncio
async def test_submit_lead_with_resume(client: AsyncClient):
    resume_content = b"%PDF-1.4 fake pdf content"
    resp = await client.post(
        "/api/leads",
        data={"first_name": "John", "last_name": "Smith", "email": "john@example.com"},
        files={"resume": ("resume.pdf", io.BytesIO(resume_content), "application/pdf")},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["resume_path"] is not None
    assert data["resume_path"].endswith(".pdf")


@pytest.mark.asyncio
async def test_submit_lead_invalid_email(client: AsyncClient):
    resp = await client.post(
        "/api/leads",
        data={"first_name": "Bad", "last_name": "Email", "email": "not-an-email"},
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
