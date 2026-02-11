import logging

import pytest

from app.services.email_service import LoggingEmailService, get_email_service


@pytest.mark.asyncio
async def test_logging_email_service(caplog):
    service = LoggingEmailService()
    with caplog.at_level(logging.INFO):
        await service.send_email(
            to="test@example.com",
            subject="Test Subject",
            body="Test body",
        )
    assert "test@example.com" in caplog.text
    assert "Test Subject" in caplog.text


def test_get_email_service_returns_logging_impl():
    service = get_email_service()
    assert isinstance(service, LoggingEmailService)
