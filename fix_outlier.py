from pymongo import MongoClient
from pprint import pprint

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["vastr_fashion_db"]
products = db["products"]

# Find outliers
print("🔍 Finding products with price_min < 100...")
outliers = list(products.find({"price_min": {"$lt": 100}}))
print(f"Found {len(outliers)} products:")
for product in outliers[:5]:  # Show first 5
    pprint({
        "product_id": product["product_id"],
        "brand_id": product["brand_id"],
        "title": product["title"],
        "price_min": product["price_min"]
    })

# Fix prices (multiply by 100)
print("\n🔧 Updating prices...")
result = products.update_many(
    {"price_min": {"$lt": 100}},
    [{"$set": {"price_min": {"$multiply": ["$price_min", 100]}, "price_max": {"$multiply": ["$price_max", 100]}}}]
)
print(f"Updated {result.modified_count} products")

# Verify
print("\n🔍 Verifying...")
outliers_after = list(products.find({"price_min": {"$lt": 100}}))
print(f"Remaining outliers: {len(outliers_after)}")
if outliers_after:
    print("Remaining outliers:")
    for product in outliers_after[:5]:
        pprint({
            "product_id": product["product_id"],
            "brand_id": product["brand_id"],
            "title": product["title"],
            "price_min": product["price_min"]
        })

client.close()