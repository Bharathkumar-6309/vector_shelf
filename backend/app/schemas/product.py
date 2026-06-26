"""Pydantic schemas for Product API."""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field


class ProductBase(BaseModel):
    """Base product schema with common fields."""
    
    name: str = Field(..., min_length=1, max_length=255, description="Product name")
    category: str = Field(..., min_length=1, max_length=100, description="Product category")
    price: Decimal = Field(..., gt=0, decimal_places=2, description="Product price")


class ProductCreate(ProductBase):
    """Schema for creating a product."""
    pass


class ProductUpdate(ProductBase):
    """Schema for updating a product."""
    pass


class ProductResponse(ProductBase):
    """Schema for product response."""
    
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ProductListResponse(BaseModel):
    """Schema for product list response with pagination."""
    
    snapshot: datetime
    products: list[ProductResponse]
    pagination: "PaginationResponse"
    category: Optional[str] = Field(None, description="Filtered category")


class CategoryListResponse(BaseModel):
    """Schema for category list response."""

    data: list[str] = Field(..., description="List of available categories")


# Forward references for circular dependencies
class PaginationResponse(BaseModel):
    """Pagination metadata."""
    
    next_cursor: Optional[str] = Field(None, description="Cursor for next page")
    has_next: bool = Field(..., description="Whether there are more pages")
    limit: int = Field(..., description="Number of items per page")
    # Keyset cursor fields (for client convenience and debugging)
    cursor_updated_at: Optional[datetime] = Field(None, description="Last item's updated_at for the next cursor")
    cursor_id: Optional[int] = Field(None, description="Last item's id for the next cursor")


class MetaResponse(BaseModel):
    """Additional metadata."""
    
    total_count: Optional[int] = Field(None, description="Total number of products")
    category: Optional[str] = Field(None, description="Filtered category")
    snapshot_at: Optional[datetime] = Field(None, description="Snapshot timestamp for consistency")


# Update forward references
ProductListResponse.model_rebuild()
