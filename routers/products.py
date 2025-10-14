from fastapi import APIRouter, HTTPException
from pymongo import MongoClient
from typing import List

router = APIRouter(prefix="/products", tags=["Products"])

MONGO_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "vastr_fashion_db"
client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]
products_col = db['products']

@router.get("/", response_model=List[dict])
def get_products(limit: int = 50):
    products = list(products_col.find().limit(limit))
    if not products:
        raise HTTPException(status_code=404, detail="No products found")
    for p in products:
        p["_id"] = str(p["_id"])
    return products

@router.get("/{product_id}")
def get_product(product_id: str):
    product = products_col.find_one({"product_id": product_id})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    product["_id"] = str(product["_id"])
    return product

@router.get("/page/{page_num}")
def get_products_page(page_num: int = 1, page_size: int = 20):
    skip = (page_num - 1) * page_size
    products = list(products_col.find().skip(skip).limit(page_size))
    for p in products:
        p["_id"] = str(p["_id"])
    return products
