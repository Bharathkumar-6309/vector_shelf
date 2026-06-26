"""Application configuration using Pydantic settings."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    Works for both local dev and Render deployment.
    """

    # Database (Render or local fallback)
    database_url: str | None = None
    sqlite_dev_url: str = "sqlite:///./dev.db"

    # App metadata
    app_name: str = "Product Browser API"
    app_version: str = "1.0.0"
    debug: bool = False

    # API limits
    max_page_size: int = 100
    default_page_size: int = 20

    # Logging
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False

    @property
    def db_url(self) -> str:
        """
        Final database URL used by the application.

        Priority:
        1. DATABASE_URL (Render PostgreSQL)
        2. SQLite fallback (local dev)
        """
        return self.database_url or self.sqlite_dev_url


settings = Settings()