
from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List, Dict
from pydantic import BaseModel, Field
import sys

sys.path.append('..')

# Import your hybrid search engine
from backend.hybrid_search import VastrHybridSearch

# Initialize search engine (singleton pattern)
search_engine = None


def get_search_engine():
    """Get or create search engine instance"""
    global search_engine
    if search_engine is None:
        search_engine = VastrHybridSearch()
    return search_engine


# ============================================
# PYDANTIC MODELS
# ============================================

class SearchFilters(BaseModel):
    """Search filters model"""
    brand_id: Optional[str] = Field(None, description="Filter by brand ID (e.g., 'nishat')")
    min_price: Optional[float] = Field(None, description="Minimum price in PKR")
    max_price: Optional[float] = Field(None, description="Maximum price in PKR")
    product_type: Optional[str] = Field(None, description="Filter by product type")
    available_only: Optional[bool] = Field(False, description="Show only available products")


class ProductResult(BaseModel):
    """Single product in search results"""
    product_id: str
    title: str
    brand_name: str
    brand_id: str
    price_min: Optional[float]
    price_max: Optional[float]
    currency: str = "PKR"
    available: bool
    url: str
    images: List[Dict]
    search_score: float
    bm25_score: float
    cosine_score: float


class SearchInsights(BaseModel):
    """Search insights and statistics"""
    brands: Dict[str, int]
    price_range: Optional[Dict[str, float]]
    product_types: Dict[str, int]


class SearchResponse(BaseModel):
    """Search API response"""
    query: str
    total_results: int
    results_shown: int
    products: List[Dict]
    insights: SearchInsights
    filters_applied: Dict


# ============================================
# ROUTER
# ============================================

router = APIRouter(
    prefix="/api/v1/search",
    tags=["Search"]
)


@router.get("/", response_model=SearchResponse)
async def search_products(
        q: str = Query(..., description="Search query (e.g., 'embroidered lawn suit')"),
        limit: int = Query(20, ge=1, le=100, description="Number of results to return"),
        brand: Optional[str] = Query(None, description="Filter by brand ID"),
        min_price: Optional[float] = Query(None, description="Minimum price in PKR"),
        max_price: Optional[float] = Query(None, description="Maximum price in PKR"),
        available_only: bool = Query(False, description="Show only available products"),
        bm25_weight: float = Query(0.5, ge=0, le=1, description="BM25 algorithm weight (0-1)"),
        cosine_weight: float = Query(0.5, ge=0, le=1, description="Cosine similarity weight (0-1)")
):
    """
    Search products using Hybrid Search (BM25 + Cosine Similarity)

    **Examples:**
    - `/api/v1/search?q=black dress`
    - `/api/v1/search?q=embroidered lawn&brand=nishat&max_price=5000`
    - `/api/v1/search?q=aesthetic top&limit=10`
    - `/api/v1/search?q=interview outfit&available_only=true`
    """
    try:
        # Build filters
        filters = {}
        if brand:
            filters['brand_id'] = brand
        if min_price:
            filters['min_price'] = min_price
        if max_price:
            filters['max_price'] = max_price
        if available_only:
            filters['available_only'] = True

        # Get search engine
        engine = get_search_engine()

        # Perform search with insights
        results = engine.search_with_insights(
            query=q,
            top_k=limit
        )

        # Apply additional filters if needed
        if filters:
            filtered_products = []
            for product in results['products']:
                if engine._apply_filters(product, filters):
                    filtered_products.append(product)
            results['products'] = filtered_products
            results['total_results'] = len(filtered_products)

        return {
            "query": q,
            "total_results": results['total_results'],
            "results_shown": len(results['products']),
            "products": results['products'],
            "insights": results['insights'],
            "filters_applied": filters
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")


@router.get("/suggestions")
async def get_search_suggestions(
        q: str = Query(..., min_length=2, description="Partial search query"),
        limit: int = Query(5, ge=1, le=10, description="Number of suggestions")
):
    """
    Get search suggestions/autocomplete

    **Example:**
    - `/api/v1/search/suggestions?q=emb` → Returns "embroidered", "embroidered lawn", etc.
    """
    try:
        engine = get_search_engine()

        # Get all unique titles containing the query
        suggestions = set()
        query_lower = q.lower()

        for product in engine.products_list:
            title = product.get('title', '').lower()
            if query_lower in title:
                # Add title
                suggestions.add(product.get('title'))

                # Add brand + title combination
                brand = product.get('brand_name', '')
                if brand:
                    suggestions.add(f"{brand} {product.get('title')}")

                # Add product type
                ptype = product.get('product_type', '')
                if ptype and query_lower in ptype.lower():
                    suggestions.add(ptype)

            if len(suggestions) >= limit * 3:
                break

        # Return top suggestions
        suggestions_list = sorted(list(suggestions))[:limit]

        return {
            "query": q,
            "suggestions": suggestions_list
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Suggestions error: {str(e)}")


@router.post("/advanced")
async def advanced_search(
        query: str,
        filters: SearchFilters,
        limit: int = Query(20, ge=1, le=100),
        bm25_weight: float = Query(0.5, ge=0, le=1),
        cosine_weight: float = Query(0.5, ge=0, le=1)
):
    """
    Advanced search with POST body for complex filters

    **Request Body Example:**
    ```json
    {
      "query": "embroidered suit",
      "filters": {
        "brand_id": "nishat",
        "min_price": 3000,
        "max_price": 8000,
        "available_only": true
      },
      "limit": 10
    }
    ```
    """
    try:
        # Convert filters to dict
        filters_dict = {k: v for k, v in filters.dict().items() if v is not None}

        # Get search engine
        engine = get_search_engine()

        # Perform hybrid search
        results = engine.hybrid_search(
            query=query,
            top_k=limit,
            bm25_weight=bm25_weight,
            cosine_weight=cosine_weight,
            filters=filters_dict
        )

        return {
            "query": query,
            "total_results": len(results),
            "filters_applied": filters_dict,
            "products": results
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Advanced search error: {str(e)}")


@router.get("/similar/{product_id}")
async def find_similar_products(
        product_id: str,
        limit: int = Query(10, ge=1, le=50, description="Number of similar products")
):
    """
    Find similar products based on a given product ID

    **Example:**
    - `/api/v1/search/similar/8492810567879?limit=5`
    """
    try:
        engine = get_search_engine()

        # Find the product
        target_product = None
        for product in engine.products_list:
            if product.get('product_id') == product_id:
                target_product = product
                break

        if not target_product:
            raise HTTPException(status_code=404, detail="Product not found")

        # Create search query from product attributes
        search_query = f"{target_product.get('title', '')} {target_product.get('product_type', '')}"

        # Search for similar products
        results = engine.hybrid_search(
            query=search_query,
            top_k=limit + 1,  # +1 to exclude the product itself
            bm25_weight=0.3,
            cosine_weight=0.7  # Emphasize semantic similarity
        )

        # Remove the target product from results
        similar_products = [p for p in results if p.get('product_id') != product_id][:limit]

        return {
            "target_product_id": product_id,
            "target_product_title": target_product.get('title'),
            "similar_products_count": len(similar_products),
            "similar_products": similar_products
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Similar products error: {str(e)}")


@router.get("/trending")
async def get_trending_searches(limit: int = Query(10, ge=1, le=20)):
    """
    Get trending/popular search terms
    (In production, this would track actual user searches)
    """
    # For now, return predefined trending terms
    trending = [
        {"term": "embroidered lawn suit", "category": "Traditional"},
        {"term": "summer collection", "category": "Seasonal"},
        {"term": "formal dress", "category": "Occasion"},
        {"term": "black dress", "category": "Color"},
        {"term": "aesthetic top", "category": "Style"},
        {"term": "bridal collection", "category": "Occasion"},
        {"term": "casual wear", "category": "Style"},
        {"term": "korean fashion", "category": "Trend"},
        {"term": "party outfit", "category": "Occasion"},
        {"term": "luxury collection", "category": "Premium"}
    ]

    return {
        "trending_searches": trending[:limit],
        "note": "Based on popular fashion trends"
    }


@router.get("/stats")
async def get_search_stats():
    """
    Get search engine statistics
    """
    try:
        engine = get_search_engine()

        return {
            "total_products_indexed": len(engine.products_list),
            "search_algorithms": ["BM25", "TF-IDF + Cosine Similarity"],
            "indexing_status": "ready",
            "supported_features": [
                "Keyword search (BM25)",
                "Semantic search (Cosine Similarity)",
                "Hybrid ranking",
                "Query expansion",
                "Style synonym matching",
                "Multi-field search",
                "Price filtering",
                "Brand filtering",
                "Availability filtering"
            ]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stats error: {str(e)}")