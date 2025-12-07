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


@router.get("/products")
async def get_products(
    limit: int = Query(20, ge=1, le=100),
    page: int = Query(1, ge=1),
    brand: Optional[str] = None,
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    search: Optional[str] = None
):
    query = {}
    if brand:
        query["brand_name"] = brand.title()
    if category:
        query["product_type"] = category
    if min_price is not None:
        query["price_min"] = {"$gte": min_price}
    if max_price is not None:
        query.setdefault("price_min", {})["$lte"] = max_price
    if search:
        query["$text"] = {"$search": search}

    skip = (page - 1) * limit
    total = products_col.count_documents(query)
    cursor = products_col.find(query).skip(skip).limit(limit)
    products = list(cursor)

    for p in products:
        p["_id"] = str(p["_id"])

    return {
        "products": products,
        "total_products": total,
        "page": page,
        "limit": limit
    }