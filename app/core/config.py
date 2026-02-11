from pathlib import Path

from pydantic_settings import BaseSettings

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    model_config = {
        "env_file": str(PROJECT_ROOT / ".env"),
        "env_file_encoding": "utf-8",
    }

    DATABASE_URL: str = "sqlite+aiosqlite:///./alma.db"
    UPLOAD_DIR: str = "uploads"

    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60

    INTERNAL_USER_USERNAME: str = "admin"
    INTERNAL_USER_PASSWORD_HASH: str = ""

    ATTORNEY_EMAILS: list[str] = ["attorney@example.com"]


settings = Settings()
