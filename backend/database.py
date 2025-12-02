# database.py
from pymongo import MongoClient
import os

# MongoDB Config
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = "vastr_fashion_db"
COLLECTION_NAME = "products"

# Global objects (will be created once)
_client = None
_db = None
_products_collection = None

def get_db_client():
    """Returns the MongoDB client (singleton)"""
    global _client
    if _client is None:
        _client = MongoClient(MONGODB_URL)
    return _client

def get_database():
    """Returns the database instance"""
    global _db
    if _db is None:
        _db = get_db_client()[DATABASE_NAME]
    return _db

def get_products_collection():
    """Returns the products collection"""
    global _products_collection
    if _products_collection is None:
        _products_collection = get_database()[COLLECTION_NAME]
    return _products_collection

def test_connection():
    """Test connection and show product count"""
    try:
        client = get_db_client()
        client.admin.command('ping')
        count = get_products_collection().count_documents({})
        print(f"MongoDB Connected!")
        print(f"Products in database: {count:,}")
        return True
    except Exception as e:
        print(f"MongoDB Connection Failed: {e}")
        return False

# Auto-test when run directly
if __name__ == "__main__":
    test_connection()