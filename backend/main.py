# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from routers import brands, general, products, search
from database import test_connection, get_db_client
# Global flag
IS_IMAGE_SEARCH_ACTIVE = False

# Import image_search AFTER other imports
from routers import image_search

# Global db reference
db = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global db
    print("=" * 50)
    print("Starting Vastr Fashion API...")
    print("=" * 50)
    
    # Test connection + get db
    test_connection()
    client = get_db_client()
    db = client["vastr_fashion_db"]
    
    print("=" * 50)
    print("API Ready!")
    print("Docs: http://localhost:8000/docs")
    print("=" * 50)
    yield
    
    # Cleanup
    client.close()
    print("=" * 50)
    print("Shutting down Vastr Fashion API...")
    print("=" * 50)

app = FastAPI(
    title="Vastr Fashion API",
    description="Backend for Pakistani Fashion Platform",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(brands.router)
app.include_router(general.router)
app.include_router(products.router)
app.include_router(search.router)
app.include_router(image_search.router)

# Add root endpoint for testing
@app.get("/")
async def root():
    return {
        "message": "Vastr Fashion API",
        "version": "1.0.0",
        "endpoints": {
            "docs": "/docs",
            "products": "/api/v1/products",
            "search": "/api/v1/search",
            "image_search": "/api/v1/search/image"
        }
    }
