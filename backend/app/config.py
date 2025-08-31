from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


# Resolve env file relative to this backend/ package regardless of CWD
BASE_DIR = Path(__file__).resolve().parent.parent  # points to backend/
ENV_FILE = BASE_DIR / "demo.env"


class Settings(BaseSettings):
    """Application settings loaded from environment and demo.env file."""

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_ignore_empty=True,
        extra="ignore",
    )

    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""

    FRONTEND_URL: str = "http://localhost:5173"
    SECURE_COOKIES: bool = False
    SECRET: str = "SECRET"
    DB_NAME: str | None = None
    COOKIE_MAX_AGE: int = 3600
    API_V1_STR: str = "/api/v1"

    @property
    def DATABASE_URL(self) -> str:
        """Return the full async SQLAlchemy database URL.

        Uses sqlite+aiosqlite and resolves a default absolute DB path
        if DB_NAME is not supplied via environment.
        """
        db_path = Path(BASE_DIR, "app", "test.db").as_posix()
        return f"sqlite+aiosqlite:///{db_path}"


@lru_cache
def get_settings() -> "Settings":
    return Settings()


# Cached settings instance for easy imports
settings = get_settings()
