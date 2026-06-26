"""Product repository with cursor-based pagination."""

from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app.models.product import Product
from app.repositories.base import BaseRepository


class ProductRepository(BaseRepository[Product]):
    """Repository for product-specific database operations."""
    
    def __init__(self, db: Session):
        super().__init__(Product, db)
    
    def get_products_with_cursor(
        self,
        limit: int,
        category: Optional[str] = None,
        cursor_updated_at: Optional[datetime] = None,
        cursor_id: Optional[int] = None,
        snapshot_at: Optional[datetime] = None
    ) -> List[Product]:
        """
        Get products using cursor-based pagination with snapshot consistency.
        
        Args:
            limit: Number of products to return
            category: Optional category filter
            cursor_updated_at: Updated timestamp from cursor (for pagination)
            cursor_id: Product ID from cursor (for pagination)
            snapshot_at: Snapshot timestamp for consistency
            
        Returns:
            List of products
        """
        query = self.db.query(Product)
        
        # Apply category filter
        if category:
            query = query.filter(Product.category == category)
        
        # Apply snapshot filter for consistency
        if snapshot_at:
            query = query.filter(Product.updated_at <= snapshot_at)
        
        # Apply cursor conditions for pagination
        if cursor_updated_at and cursor_id:
            # Use strict inequality to avoid duplicates
            # (updated_at < cursor_updated_at) OR (updated_at = cursor_updated_at AND id < cursor_id)
            cursor_condition = or_(
                Product.updated_at < cursor_updated_at,
                and_(
                    Product.updated_at == cursor_updated_at,
                    Product.id < cursor_id
                )
            )
            query = query.filter(cursor_condition)
        
        # Order by updated_at DESC, id DESC for newest-first with stable ordering
        query = query.order_by(Product.updated_at.desc(), Product.id.desc())
        
        # Limit results
        query = query.limit(limit)
        
        return query.all()
    
    def count_by_category(self, category: Optional[str] = None) -> int:
        """
        Count products, optionally filtered by category.
        
        Args:
            category: Optional category filter
            
        Returns:
            Number of products
        """
        query = self.db.query(Product)
        
        if category:
            query = query.filter(Product.category == category)
        
        return query.count()
    
    def get_distinct_categories(self) -> List[str]:
        """
        Get all distinct categories.
        
        Returns:
            List of category names
        """
        result = self.db.query(Product.category).distinct().all()
        return [row[0] for row in result]
