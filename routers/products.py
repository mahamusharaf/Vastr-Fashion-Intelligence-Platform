from fastapi import APIRouter
from typing import List
from database import get_products_collection   # ← THIS IS THE ONLY THING THAT MATTERS

router = APIRouter(prefix="/products", tags=["Products"])

# THIS IS THE ONLY LINE THAT COUNTS
products_col = get_products_collection()

@router.get("/")
async def get_products(limit: int = 5):
    print("\nDEBUG: Using collection →", products_col.name)           # ← WILL SHOW "products"
    print("DEBUG: Database name →", products_col.database.name)       # ← WILL SHOW "vastr"
    count = products_col.count_documents({})
    print(f"DEBUG: TOTAL PRODUCTS IN DB = {count}\n")                # ← MUST SHOW 12364

    cursor = products_col.find().limit(limit)
    products = list(cursor)
    
    print(f"DEBUG: Actually fetched {len(products)} products")       # ← MUST BE > 0

    for p in products:
        p["_id"] = str(p["_id"])

    return {
        "products": products,
        "total_products": count,
        "page": 1,
        "limit": limit
    }