from pymongo import MongoClient

# FIXED & FINAL — NO IMPORTS FROM ANYWHERE ELSE
MONGODB_URL = "mongodb://localhost:27017"
DATABASE_NAME = "vastr"        # ← This is where we inserted 12,364 products
COLLECTION_NAME = "products"   # ← This is the correct collection name

# Create MongoDB client
client = MongoClient(MONGODB_URL)
db = client[DATABASE_NAME]
products_collection = db[COLLECTION_NAME]


def get_database():
    """Returns the database instance"""
    return db


def get_products_collection():
    """Returns the products collection"""
    return products_collection


def test_connection():
    """Test MongoDB connection"""
    try:
        client.admin.command('ping')
        count = products_collection.count_documents({})
        print(f"MongoDB connected! Found {count} products")
        return True
    except Exception as e:
        print(f"MongoDB connection failed: {e}")
        return False


if __name__ == "__main__":
    test_connection()