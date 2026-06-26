"""Unit tests for product service."""

import pytest
from datetime import datetime, timedelta
from app.services.product_service import ProductService
from app.utils.cursor import decode_cursor
from app.models.product import Product


class TestProductServiceGetProducts:
    """Tests for ProductService.get_products method."""
    
    def test_first_page_no_cursor(self, test_db, sample_products):
        """Test loading first page without cursor."""
        service = ProductService(test_db)
        
        result = service.get_products(limit=20)
        
        assert result is not None
        assert len(result.products) == 20
        assert result.pagination.has_next is True
        assert result.pagination.next_cursor is not None
        assert result.pagination.limit == 20
        assert result.snapshot is not None
    
    def test_first_page_generates_snapshot(self, test_db, sample_products):
        """Test that first page generates a snapshot timestamp."""
        service = ProductService(test_db)
        
        result = service.get_products(limit=20)
        
        assert result.snapshot is not None
        assert isinstance(result.snapshot, datetime)
        # Snapshot should be recent (within last minute)
        assert datetime.utcnow() - result.snapshot < timedelta(minutes=1)
    
    def test_second_page_with_cursor(self, test_db, sample_products):
        """Test loading second page with cursor from first page."""
        service = ProductService(test_db)
        
        # Get first page
        page1 = service.get_products(limit=20)
        
        # Get second page using cursor and snapshot
        page2 = service.get_products(limit=20, cursor=page1.pagination.next_cursor, snapshot=page1.snapshot)
        
        assert len(page2.products) == 20
        assert page2.pagination.has_next is True
        assert page2.pagination.next_cursor is not None
        # Verify different products
        page1_ids = {p.id for p in page1.products}
        page2_ids = {p.id for p in page2.products}
        assert len(page1_ids.intersection(page2_ids)) == 0  # No duplicates
    
    def test_cursor_contains_snapshot(self, test_db, sample_products):
        """Test that cursor includes snapshot timestamp."""
        service = ProductService(test_db)
        
        page1 = service.get_products(limit=20)
        page2 = service.get_products(limit=20, cursor=page1.pagination.next_cursor, snapshot=page1.snapshot)
        
        # Decode cursor to check snapshot
        cursor_data = decode_cursor(page2.pagination.next_cursor)
        assert "snapshot_at" in cursor_data
        assert cursor_data["snapshot_at"] == page1.snapshot
    
    def test_snapshot_remains_constant(self, test_db, sample_products):
        """Test that snapshot timestamp remains constant across pages."""
        service = ProductService(test_db)
        
        page1 = service.get_products(limit=20)
        page2 = service.get_products(limit=20, cursor=page1.pagination.next_cursor, snapshot=page1.snapshot)
        page3 = service.get_products(limit=20, cursor=page2.pagination.next_cursor, snapshot=page2.snapshot)
        
        assert page1.snapshot == page2.snapshot
        assert page2.snapshot == page3.snapshot
    
    def test_category_filter(self, test_db, sample_products):
        """Test filtering by category."""
        service = ProductService(test_db)
        
        result = service.get_products(limit=20, category="Electronics")
        
        assert len(result.products) <= 20
        assert result.category == "Electronics"
        # All products should be Electronics
        for product in result.products:
            assert product.category == "Electronics"
    
    def test_empty_category(self, test_db, sample_products):
        """Test filtering by non-existent category."""
        service = ProductService(test_db)
        
        result = service.get_products(limit=20, category="NonExistentCategory")
        
        assert len(result.products) == 0
        assert result.pagination.has_next is False
        assert result.pagination.next_cursor is None
        assert result.category == "NonExistentCategory"
    
    def test_invalid_cursor(self, test_db, sample_products):
        """Test handling of invalid cursor."""
        service = ProductService(test_db)
        
        with pytest.raises(ValueError, match="Invalid cursor format"):
            service.get_products(limit=20, cursor="invalid_cursor_string", snapshot=datetime.utcnow().isoformat())
    
    def test_limit_validation(self, test_db, sample_products):
        """Test that limit parameter works correctly."""
        service = ProductService(test_db)
        
        result5 = service.get_products(limit=5)
        result10 = service.get_products(limit=10)
        
        assert len(result5.products) == 5
        assert len(result10.products) == 10
    
    def test_last_page_no_next_cursor(self, test_db):
        """Test that last page has no next cursor."""
        # Create exactly 25 products
        from decimal import Decimal
        for i in range(25):
            product = Product(
                name=f"Product {i}",
                category="Electronics",
                price=Decimal(str(10.0 + i)),
                created_at=datetime.utcnow() - timedelta(hours=i),
                updated_at=datetime.utcnow() - timedelta(hours=i)
            )
            test_db.add(product)
        test_db.commit()
        
        service = ProductService(test_db)
        
        # First page with limit 20
        page1 = service.get_products(limit=20)
        assert page1.pagination.has_next is True
        
        # Second page with limit 20 (should have 5 items)
        page2 = service.get_products(limit=20, cursor=page1.pagination.next_cursor, snapshot=page1.snapshot)
        assert len(page2.products) == 5
        assert page2.pagination.has_next is False
        assert page2.pagination.next_cursor is None
    
    def test_products_ordered_by_updated_at_desc(self, test_db, sample_products):
        """Test that products are ordered by updated_at DESC, id DESC."""
        service = ProductService(test_db)
        
        result = service.get_products(limit=20)
        
        # Check ordering
        for i in range(len(result.products) - 1):
            current = result.products[i]
            next_item = result.products[i + 1]
            # updated_at should be descending
            assert current.updated_at >= next_item.updated_at
            # If updated_at is equal, id should be descending
            if current.updated_at == next_item.updated_at:
                assert current.id > next_item.id


class TestProductServiceGetCategories:
    """Tests for ProductService.get_categories method."""
    
    def test_get_categories(self, test_db, sample_products):
        """Test getting all distinct categories."""
        service = ProductService(test_db)
        
        categories = service.get_categories()
        
        assert categories is not None
        assert isinstance(categories, list)
        assert len(categories) > 0
        assert "Electronics" in categories
        assert "Fashion" in categories
    
    def test_get_categories_empty_database(self, test_db):
        """Test getting categories from empty database."""
        service = ProductService(test_db)
        
        categories = service.get_categories()
        
        assert categories == []
