"""Common schemas for API responses."""

from typing import Optional, Any
from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """Standard error response schema."""
    
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    status_code: int = Field(..., description="HTTP status code")


class SuccessResponse(BaseModel):
    """Standard success response schema."""
    
    message: str = Field(..., description="Success message")
    data: Optional[Any] = Field(None, description="Response data")
