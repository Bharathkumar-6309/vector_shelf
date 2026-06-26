"""Database connection and session management (Render-safe)."""

from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import logging

from app.core.config import settings
from app.models.product import Product
from app.models.base import Base

logger = logging.getLogger(__name__)


def get_database_url() -> str:
    """
    Get database URL with proper fallback:
    1. Render PostgreSQL (DATABASE_URL)
    2. Local SQLite (dev.db)
    """
    if settings.database_url:
        return settings.database_url

    local_db_path = Path(__file__).resolve().parents[2] / "dev.db"
    fallback_url = f"sqlite:///{local_db_path}"

    logger.warning(
        "DATABASE_URL not set. Using SQLite fallback: %s",
        fallback_url,
    )
    return fallback_url


# Create engine (Render + local safe)
engine = create_engine(
    get_database_url(),
    pool_pre_ping=True,
    echo=settings.debug,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def get_db() -> Generator[Session, None, None]:
    """Yield database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Initialize DB and seed data if needed."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))

        logger.info("Database connection successful")

        Base.metadata.create_all(bind=engine)
        logger.info("Tables created/verified")

        # Seed only for SQLite
        if str(engine.url).startswith("sqlite"):
            with SessionLocal() as session:
                count = session.query(Product).count()
                if count == 0:
                    session.add_all([
                        Product(name="Modern Art Print", category="art", price=29.99),
                        Product(name="Icon Bundle", category="icons", price=14.99),
                        Product(name="Stock Photo Pack", category="photos", price=49.99),
                        Product(name="Geometric Shape Set", category="shapes", price=19.99),
                    ])
                    session.commit()
                    logger.info("Seeded SQLite database")

    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise