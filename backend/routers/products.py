# routers/products.py  ← THIS IS THE ONLY ONE YOU NEED
from fastapi import APIRouter, Query
from typing import List, Optional
from pymongo import MongoClient

router = APIRouter(prefix="/api/v1")

client = MongoClient("mongodb://localhost:27017")
db = client["vastr_fashion_db"]
products_col = db["products"]

@router.get("/products")
async def get_products(
    limit: int = Query(24, le=100),
    page: int = Query(1),
    brand: Optional[List[str]] = Query(None),
    category: Optional[List[str]] = Query(None),
    sort: Optional[str] = Query(None),
):
    query = {}
    if brand:
        query["brand_name"] = {"$in": brand}
    if category:
        query["product_type"] = {"$in": category}

    sort_key, sort_dir = "_id", -1
    if sort == "price_asc":
        sort_key, sort_dir = "price_min", 1
    elif sort == "price_desc":
        sort_key, sort_dir = "price_min", -1

    skip = (page - 1) * limit
    total = products_col.count_documents(query)
    products = list(products_col.find(query).sort(sort_key, sort_dir).skip(skip).limit(limit))

    for p in products:
        p["_id"] = str(p["_id"])

    return {"products": products, "total_products": total}


@router.get("/brands")
async def get_brands():
    pipeline = [{"$group": {"_id": "$brand_name", "count": {"$sum": 1}}}]
    result = []
    for b in products_col.aggregate(pipeline):
        name = b["_id"]
        result.append({
            "brand_id": name.lower().replace(" ", "-").replace("&", "and"),
            "brand_name": name,
            "product_count": b["count"]
        })
    result.sort(key=lambda x: x["brand_name"])
    return {"brands": result}