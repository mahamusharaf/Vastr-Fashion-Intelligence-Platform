# routers/products.py  ← THIS IS THE ONLY ONE YOU NEED
from fastapi import APIRouter, Query, HTTPException
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
        price_min: Optional[int] = Query(None),
        price_max: Optional[int] = Query(None),
        sort: Optional[str] = Query(None),
):
    query = {}

    # Brand filter
    if brand:
        query["brand_name"] = {"$in": brand}

    # Category filter
    if category:
        query["product_type"] = {"$in": category}

    # Price filter
    if price_min is not None or price_max is not None:
        query["price_min"] = {}
        if price_min is not None:
            query["price_min"]["$gte"] = price_min
        if price_max is not None:
            query["price_min"]["$lte"] = price_max

    # Sorting
    sort_key, sort_dir = "_id", -1
    if sort == "price_asc":
        sort_key, sort_dir = "price_min", 1
    elif sort == "price_desc":
        sort_key, sort_dir = "price_min", -1

    # Pagination
    skip = (page - 1) * limit

    # Execute query
    total = products_col.count_documents(query)
    products = list(
        products_col.find(query)
        .sort(sort_key, sort_dir)
        .skip(skip)
        .limit(limit)
    )

    # Convert ObjectId to string
    for p in products:
        p["_id"] = str(p["_id"])

    return {
        "products": products,
        "total_products": total,
        "page": page,
        "limit": limit
    }


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


@router.get("/products/{product_id}")
async def get_product_by_id(product_id: str):
    """Get a single product by ID"""
    try:
        # Try to find by product_id field
        product = products_col.find_one({"product_id": product_id})

        # If not found, try by _id (MongoDB ObjectId)
        if not product:
            from bson import ObjectId
            if ObjectId.is_valid(product_id):
                product = products_col.find_one({"_id": ObjectId(product_id)})

        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        # Convert ObjectId to string
        product["_id"] = str(product["_id"])

        return product
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))