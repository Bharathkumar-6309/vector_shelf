"""Product API endpoints."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.product_service import ProductService
from app.schemas.product import ProductListResponse, CategoryListResponse
from app.config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/products", response_model=ProductListResponse)
async def get_products(
    limit: int = Query(default=settings.default_page_size, ge=1, le=settings.max_page_size, description="Number of products per page"),
    category: Optional[str] = Query(default=None, description="Filter by category"),
    cursor: Optional[str] = Query(default=None, description="Cursor for pagination"),
    snapshot: Optional[str] = Query(default=None, description="Snapshot timestamp for pagination consistency"),
    db: Session = Depends(get_db)
) -> ProductListResponse:
    """
    Get products with cursor-based pagination and snapshot consistency.
    
    Args:
        limit: Number of products to return (1-100)
        category: Optional category filter
        cursor: Optional cursor string for pagination (from previous response)
        db: Database session
        
    Returns:
        ProductListResponse with products and pagination metadata
        
    Raises:
        HTTPException: If cursor is invalid
    """
    try:
        service = ProductService(db)
        result = service.get_products(
            limit=limit,
            category=category,
            cursor=cursor,
            snapshot=snapshot
        )
        logger.info(f"Retrieved {len(result.products)} products with cursor={cursor}")
        return result
    except ValueError as e:
        logger.error(f"Invalid cursor: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error fetching products: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/categories", response_model=CategoryListResponse)
async def get_categories(
    db: Session = Depends(get_db)
) -> CategoryListResponse:
    """
    Get all distinct product categories.
    
    Args:
        db: Database session
        
    Returns:
        CategoryListResponse with list of categories
    """
    try:
        service = ProductService(db)
        categories = service.get_categories()
        logger.info(f"Retrieved {len(categories)} categories")
        return CategoryListResponse(data=categories)
    except Exception as e:
        logger.error(f"Error fetching categories: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
