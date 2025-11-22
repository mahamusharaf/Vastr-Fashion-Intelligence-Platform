from fastapi import APIRouter, HTTPException, status
from typing import List
import sys

sys.path.append('..')

from database import get_products_collection
from models.brand import (
    BrandsListResponse,
    BrandDetail,
    CategoriesListResponse,
    CategoryBreakdown,
    PriceRange
)

router = APIRouter(
    prefix="/api/v1",
    tags=["Brands & Categories"]
)


@router.get("/brands", response_model=BrandsListResponse)
async def get_all_brands():
    """Get all brands with product counts"""
    try:
        collection = get_products_collection()

        pipeline = [
            {
                "$group": {
                    "_id": "$brand_id",
                    "brand_name": {"$first": "$brand_name"},
                    "product_count": {"$sum": 1}
                }
            },
            {"$sort": {"product_count": -1}},
            {
                "$project": {
                    "_id": 0,
                    "brand_id": "$_id",
                    "brand_name": 1,
                    "product_count": 1
                }
            }
        ]

        brands = list(collection.aggregate(pipeline))

        if not brands:
            raise HTTPException(status_code=404, detail="No brands found")

        return {
            "total_brands": len(brands),
            "brands": brands
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/brands/{brand_id}", response_model=BrandDetail)
async def get_brand_details(brand_id: str):
    """Get details for a specific brand"""
    try:
        collection = get_products_collection()

        # Check if brand exists
        if not collection.find_one({"brand_id": brand_id}):
            raise HTTPException(status_code=404, detail=f"Brand '{brand_id}' not found")

        pipeline = [
            {"$match": {"brand_id": brand_id}},
            {
                "$facet": {
                    "brand_info": [
                        {
                            "$group": {
                                "_id": "$brand_id",
                                "brand_name": {"$first": "$brand_name"},
                                "product_count": {"$sum": 1}
                            }
                        }
                    ],
                    "categories": [
                        {
                            "$group": {
                                "_id": "$product_type",
                                "count": {"$sum": 1}
                            }
                        },
                        {"$sort": {"count": -1}},
                        {
                            "$project": {
                                "_id": 0,
                                "category": "$_id",
                                "count": 1
                            }
                        }
                    ],
                    "price_stats": [
                        {
                            "$group": {
                                "_id": None,
                                "min_price": {"$min": "$price_min"},
                                "max_price": {"$max": "$price_min"},
                                "avg_price": {"$avg": "$price_min"}
                            }
                        }
                    ]
                }
            }
        ]

        result = list(collection.aggregate(pipeline))
        brand_info = result[0]["brand_info"][0]
        categories = result[0]["categories"]
        price_stats = result[0]["price_stats"][0] if result[0]["price_stats"] else {}

        return {
            "brand_id": brand_id,
            "brand_name": brand_info["brand_name"],
            "product_count": brand_info["product_count"],
            "categories_available": categories,
            "price_range": {
                "min": round(price_stats.get("min_price", 0), 2),
                "max": round(price_stats.get("max_price", 0), 2),
                "average": round(price_stats.get("avg_price", 0), 2),
                "currency": "PKR"
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/categories", response_model=CategoriesListResponse)
async def get_all_categories():
    """Get all categories with statistics"""
    try:
        collection = get_products_collection()
        total_products = collection.count_documents({})

        if total_products == 0:
            raise HTTPException(status_code=404, detail="No products found")

        pipeline = [
            {
                "$group": {
                    "_id": "$product_type",
                    "product_count": {"$sum": 1},
                    "avg_price": {"$avg": "$price_min"}
                }
            },
            {"$sort": {"product_count": -1}},
            {
                "$project": {
                    "_id": 0,
                    "category_name": "$_id",
                    "product_count": 1,
                    "avg_price": {"$round": ["$avg_price", 2]}
                }
            }
        ]

        categories = list(collection.aggregate(pipeline))

        for category in categories:
            percentage = (category["product_count"] / total_products) * 100
            category["percentage"] = round(percentage, 1)
            category["currency"] = "PKR"

        return {
            "total_categories": len(categories),
            "total_products": total_products,
            "categories": categories
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")