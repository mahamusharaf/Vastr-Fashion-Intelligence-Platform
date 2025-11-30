from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from routers import brands, general, products,search
from database import test_connection

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("=" * 50)
    print("🚀 Starting Vastr Fashion API...")
    print("=" * 50)
    test_connection()
    print("=" * 50)
    print("✅ API Ready!")
    print("📚 Docs: http://localhost:8000/docs")
    print("=" * 50)
    yield
    print("=" * 50)
    print("🛑 Shutting down Vastr Fashion API...")
    print("=" * 50)

app = FastAPI(
    title="Vastr Fashion API",
    description="Backend for Pakistani Fashion Platform",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS
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