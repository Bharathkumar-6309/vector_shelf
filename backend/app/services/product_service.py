"""Product service layer with business logic."""

from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.repositories.product_repository import ProductRepository
from app.schemas.product import ProductResponse, ProductListResponse, PaginationResponse
from app.utils.cursor import create_cursor, decode_cursor
import logging

logger = logging.getLogger(__name__)


class ProductService:
    """Service for product business logic."""
    
    def __init__(self, db: Session):
        """
        Initialize product service.
        
        Args:
            db: Database session
        """
        self.repository = ProductRepository(db)
    
    def get_products(
        self,
        limit: int,
        category: Optional[str] = None,
        cursor: Optional[str] = None,
        snapshot: Optional[str | datetime] = None
    ) -> ProductListResponse:
        """
        Get products with cursor-based pagination and snapshot consistency.
        
        Args:
            limit: Number of products per page
            category: Optional category filter
            cursor: Optional cursor string for pagination
            
        Returns:
            ProductListResponse with products and pagination metadata
        """
        # Decode cursor if provided
        cursor_updated_at = None
        cursor_id = None
        snapshot_at = None
        
        if cursor:
            if snapshot is None:
                logger.error("Snapshot is required when using cursor")
                raise ValueError("Snapshot query parameter is required for pagination continuation")
            try:
                cursor_data = decode_cursor(cursor)
                cursor_updated_at = cursor_data.get("updated_at")
                cursor_id = cursor_data.get("id")
                cursor_snapshot_at = cursor_data.get("snapshot_at")
                logger.debug(f"Decoded cursor: updated_at={cursor_updated_at}, id={cursor_id}, snapshot_at={cursor_snapshot_at}")
            except ValueError as e:
                logger.error(f"Invalid cursor: {e}")
                raise ValueError("Invalid cursor format")
            if isinstance(snapshot, datetime):
                snapshot_at = snapshot
            else:
                try:
                    snapshot_at = datetime.fromisoformat(snapshot)
                except Exception as e:
                    logger.error(f"Invalid snapshot format: {e}")
                    raise ValueError("Invalid snapshot format")
            if snapshot_at != cursor_snapshot_at:
                logger.error("Snapshot mismatch between cursor and snapshot query parameter")
                raise ValueError("Snapshot must match the cursor snapshot")
        else:
            # First page or direct snapshot-based session start
            if snapshot is not None:
                if isinstance(snapshot, datetime):
                    snapshot_at = snapshot
                else:
                    try:
                        snapshot_at = datetime.fromisoformat(snapshot)
                    except Exception as e:
                        logger.error(f"Invalid snapshot format: {e}")
                        raise ValueError("Invalid snapshot format")

        # Generate snapshot if not provided (first page)
        if snapshot_at is None:
            snapshot_at = datetime.utcnow()
            logger.debug(f"Generated new snapshot: {snapshot_at}")
        
        # Fetch products from repository
        products = self.repository.get_products_with_cursor(
            limit=limit,
            category=category,
            cursor_updated_at=cursor_updated_at,
            cursor_id=cursor_id,
            snapshot_at=snapshot_at
        )
        
        # Determine if there are more pages
        has_next = len(products) == limit
        
        # Create next cursor if there are more products
        next_cursor = None
        if has_next and products:
            last_product = products[-1]
            next_cursor = create_cursor(
                updated_at=last_product.updated_at,
                id=last_product.id,
                snapshot_at=snapshot_at
            )
        
        # Build response objects
        product_responses = [ProductResponse.model_validate(p) for p in products]
        
        # Determine cursor_updated_at and cursor_id for pagination metadata
        cursor_updated_at_for_meta = None
        cursor_id_for_meta = None
        if has_next and products:
            last_product = products[-1]
            cursor_updated_at_for_meta = last_product.updated_at
            cursor_id_for_meta = last_product.id

        return ProductListResponse(
            snapshot=snapshot_at,
            products=product_responses,
            pagination=PaginationResponse(
                next_cursor=next_cursor,
                has_next=has_next,
                limit=limit,
                cursor_updated_at=cursor_updated_at_for_meta,
                cursor_id=cursor_id_for_meta,
            ),
            category=category
        )
    
    def get_categories(self) -> list[str]:
        """
        Get all distinct categories.
        
        Returns:
            List of category names
        """
        return self.repository.get_distinct_categories()
