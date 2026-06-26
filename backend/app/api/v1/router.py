"""API v1 router aggregation."""

from fastapi import APIRouter
from app.api.v1.endpoints import products

router = APIRouter()

router.include_router(products.router, tags=["products"])
