"""
Pydantic Models for API Responses
"""

from pydantic import BaseModel, Field
from typing import List


class BrandSummary(BaseModel):
    """Model for brand in list"""
    brand_id: str
    brand_name: str
    product_count: int


class CategoryBreakdown(BaseModel):
    """Category info within a brand"""
    category: str
    count: int


class PriceRange(BaseModel):
    """Price statistics"""
    min: float
    max: float
    average: float
    currency: str = "PKR"


class BrandDetail(BaseModel):
    """Detailed brand information"""
    brand_id: str
    brand_name: str
    product_count: int
    categories_available: List[CategoryBreakdown]
    price_range: PriceRange


class CategorySummary(BaseModel):
    """Model for category"""
    category_name: str
    product_count: int
    percentage: float
    avg_price: float
    currency: str = "PKR"


class BrandsListResponse(BaseModel):
    """Response for /brands endpoint"""
    total_brands: int
    brands: List[BrandSummary]


class CategoriesListResponse(BaseModel):
    """Response for /categories endpoint"""
    total_categories: int
    total_products: int
    categories: List[CategorySummary]