from fastapi import APIRouter
from database import test_connection

router = APIRouter(
    tags=["General"]
)

@router.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to Vastr Fashion API!",
        "docs": "Visit /docs for API documentation"
    }

@router.get("/health")
async def health_check():
    """Health check"""
    db_status = test_connection()
    return {
        "api_status": "healthy",
        "database_status": "connected" if db_status else "disconnected"
    }