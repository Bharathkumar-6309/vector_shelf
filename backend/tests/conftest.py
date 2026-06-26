"""Pytest configuration and fixtures."""

import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from decimal import Decimal
from unittest.mock import patch
# Mock init_db to prevent PostgreSQL connection attempts during testing
patch("app.core.database.init_db").start()

from app.main import app
from app.models.base import Base
from app.models.product import Product
from app.core.database import get_db


# Test database URL (SQLite for testing)
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def test_engine():
    """Create test database engine."""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def test_db(test_engine):
    """Create test database session."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()


@pytest.fixture(scope="function")
def test_client(test_db):
    """Create test client with database dependency override."""
    def override_get_db():
        try:
            yield test_db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def sample_products(test_db):
    """Create sample products for testing."""
    products = []
    categories = ["Electronics", "Fashion", "Books", "Sports", "Home", "Beauty", "Automotive", "Toys"]
    
    base_time = datetime.utcnow()
    
    for i in range(100):
        product = Product(
            name=f"Product {i}",
            category=categories[i % len(categories)],
            price=Decimal(str(10.0 + i)),
            created_at=base_time - timedelta(hours=i),
            updated_at=base_time - timedelta(hours=i)
        )
        test_db.add(product)
        products.append(product)
    
    test_db.commit()
    return products


@pytest.fixture(scope="function")
def sample_products_with_same_timestamp(test_db):
    """Create products with same timestamp to test tiebreaker logic."""
    products = []
    base_time = datetime.utcnow()
    
    for i in range(20):
        product = Product(
            name=f"Product {i}",
            category="Electronics",
            price=Decimal(str(10.0 + i)),
            created_at=base_time,
            updated_at=base_time  # Same timestamp for all
        )
        test_db.add(product)
        products.append(product)
    
    test_db.commit()
    return products
