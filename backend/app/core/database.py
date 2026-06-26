"""Database connection and session management."""

from pathlib import Path
from sqlalchemy import create_engine, text, select
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from typing import Generator
import logging

from app.core.config import settings
from app.models.product import Product

logger = logging.getLogger(__name__)


def get_database_url() -> str:
    """Return the configured database URL or fallback to SQLite for local dev."""
    database_url = settings.resolved_database_url
    if settings.database_url is None:
        local_db_path = Path(__file__).resolve().parents[2] / "dev.db"
        database_url = f"sqlite:///{local_db_path}"
        logger.warning(
            "DATABASE_URL is not set; falling back to local SQLite database: %s",
            database_url,
        )
    return database_url


# Create engine with connection pooling
engine = create_engine(
    get_database_url(),
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # Verify connections before using
    echo=settings.debug,  # Log SQL queries in debug mode
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency for getting database sessions.
    
    Yields:
        Session: SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def init_db() -> None:
    """Initialize database connection, verify connectivity, and create missing tables."""
    try:
        with engine.connect() as conn:
            # Use SQLAlchemy text() for executing raw SQL in SQLAlchemy 2.x
            conn.execute(text("SELECT 1"))
        logger.info("Database connection established successfully")

        # Create database tables if they do not already exist.
        # This is useful for local dev and SQLite usage where migrations are not applied.
        from app.models.base import Base
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables verified/created successfully")

        # If we are using a local SQLite database and it is empty, seed sample products.
        db_url = str(engine.url)
        if db_url.startswith("sqlite"):
            with SessionLocal() as session:
                count = session.query(Product).count()
                if count == 0:
                    sample_products = [
                        Product(name="Modern Art Print", category="art", price=29.99),
                        Product(name="Icon Bundle", category="icons", price=14.99),
                        Product(name="Stock Photo Pack", category="photos", price=49.99),
                        Product(name="Geometric Shape Set", category="shapes", price=19.99),
                    ]
                    session.add_all(sample_products)
                    session.commit()
                    logger.info("Seeded local SQLite database with sample products")
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        raise
