from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import products

app = FastAPI(title="Vastr Fashion API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(products.router)
