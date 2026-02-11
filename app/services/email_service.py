import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class EmailService(ABC):
    @abstractmethod
    async def send_email(self, to: str, subject: str, body: str) -> None: ...


class LoggingEmailService(EmailService):
    async def send_email(self, to: str, subject: str, body: str) -> None:
        print(f"sent email to: {to}")
        logger.info("EMAIL to=%s subject=%r body=%r", to, subject, body)


def get_email_service() -> EmailService:
    return LoggingEmailService()
