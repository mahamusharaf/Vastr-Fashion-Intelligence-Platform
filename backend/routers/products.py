# routers/products.py - COMPLETE WORKING VERSION
from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional
from pymongo import MongoClient
from bson import ObjectId
import sys

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
    # Build query
    query = {}

    # Brand filter
    if brand:
        query["brand_name"] = {"$in": brand}

    # Category filter
    if category:
        query["product_type"] = {"$in": category}

    # Price filter - WORKING VERSION
    if price_min is not None and price_max is not None:
        # Both min and max specified
        query["price_min"] = {"$gte": price_min, "$lte": price_max}
    elif price_min is not None:
        # Only min specified (e.g., "Over 10000")
        query["price_min"] = {"$gte": price_min}
    elif price_max is not None:
        # Only max specified (e.g., "Under 3000")
        query["price_min"] = {"$lte": price_max}

    # Sorting
    sort_key, sort_dir = "_id", -1
    if sort == "price_asc":
        sort_key, sort_dir = "price_min", 1
    elif sort == "price_desc":
        sort_key, sort_dir = "price_min", -1

    # Pagination
    skip = (page - 1) * limit

    # DEBUG OUTPUT - MUST SEE THIS IN TERMINAL
    print("\n" + "="*80, file=sys.stderr, flush=True)
    print(f" QUERY: {query}", file=sys.stderr, flush=True)
    print(f" FILTERS: brands={brand}, categories={category}", file=sys.stderr, flush=True)
    print(f" PRICE: min={price_min}, max={price_max}", file=sys.stderr, flush=True)
    print(f" PAGINATION: page={page}, skip={skip}, limit={limit}", file=sys.stderr, flush=True)
    print("="*80 + "\n", file=sys.stderr, flush=True)

    # Execute query
    total = products_col.count_documents(query)
    products = list(
        products_col.find(query)
        .sort(sort_key, sort_dir)
        .skip(skip)
        .limit(limit)
    )

    # DEBUG RESULTS
    print(f" FOUND: {len(products)} products (Total: {total})", file=sys.stderr, flush=True)
    if products and len(products) > 0:
        print(f"   First product: {products[0].get('title', 'No title')[:50]} - PKR {products[0].get('price_min', 'N/A')}", file=sys.stderr, flush=True)
        print(f"   Last product: {products[-1].get('title', 'No title')[:50]} - PKR {products[-1].get('price_min', 'N/A')}", file=sys.stderr, flush=True)

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
    pipeline = [
        {"$group": {"_id": "$brand_name", "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}}
    ]
    result = []
    for b in products_col.aggregate(pipeline):
        name = b["_id"]
        result.append({
            "brand_id": name.lower().replace(" ", "-").replace("&", "and"),
            "brand_name": name,
            "product_count": b["count"]
        })
    return {"brands": result}


@router.get("/categories")
async def get_categories():
    pipeline = [
        {"$group": {"_id": "$product_type", "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}}
    ]
    result = []
    for c in products_col.aggregate(pipeline):
        if c["_id"]:
            result.append({
                "category_id": c["_id"].lower().replace(" ", "-"),
                "category_name": c["_id"],
                "product_count": c["count"]
            })
    return {"categories": result}


@router.get("/products/{product_id}")
async def get_product_by_id(product_id: str):
    try:
        product = products_col.find_one({"product_id": product_id})
        if not product and ObjectId.is_valid(product_id):
            product = products_col.find_one({"_id": ObjectId(product_id)})
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        product["_id"] = str(product["_id"])
        return product
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
