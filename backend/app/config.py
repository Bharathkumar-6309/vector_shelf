"""Application configuration using Pydantic settings."""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    database_url: Optional[str] = None
    sqlite_dev_url: str = "sqlite:///./dev.db"
    
    # Application
    app_name: str = "Product Browser API"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # API
    max_page_size: int = 100
    default_page_size: int = 20
    
    # Logging
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

    @property
    def resolved_database_url(self) -> str:
        """Return production DB URL or fallback to local SQLite for dev."""
        return self.database_url or self.sqlite_dev_url


settings = Settings()
