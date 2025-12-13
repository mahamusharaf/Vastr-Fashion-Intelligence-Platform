from fastapi import APIRouter, Query
from database import get_products_collection
from typing import Optional

router = APIRouter(prefix="/api/v1", tags=["General"])

# THIS IS THE ONLY LINE THAT MATTERS — USES THE CORRECT DB
products_col = get_products_collection()


@router.get("/")
async def root():
    return {
        "message": "Welcome to Vastr Fashion API!",
        "docs": "Visit /docs for API documentation"
    }


@router.get("/health")
async def health_check():
    try:
        count = products_col.count_documents({})
        return {
            "api_status": "healthy",
            "database": "vastr",
            "total_products": count
        }
    except:
        return {"api_status": "error", "database": "disconnected"}


