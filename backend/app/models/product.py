"""Product ORM model."""

from sqlalchemy import Column, String, Numeric, Index
from app.models.base import BaseModel


class Product(BaseModel):
    """Product model."""
    
    __tablename__ = "products"
    __table_args__ = (
        # Composite index for pagination by updated_at DESC, id DESC
        Index("idx_products_cursor", "updated_at", "id"),
        # Composite index to support category filtering + cursor
        Index("idx_products_category_cursor", "category", "updated_at", "id"),
    )
    
    name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    
    def __repr__(self) -> str:
        return f"<Product(id={self.id}, name='{self.name}', category='{self.category}', price={self.price})>"
