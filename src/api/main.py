"""
E-commerce Product Data Aggregation API
MCP-ready for AI shopping agents
"""

import os
from datetime import datetime, timedelta
from typing import List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

from src.models.product import (
    Product,
    ProductSearchQuery,
    ProductSearchResponse,
    ProductCategory,
    PriceAlert
)
from src.utils.data_manager import DataManager

load_dotenv()

# Initialize data manager
data_manager = DataManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown"""
    print("🛒 E-commerce Product API starting...")
    await data_manager.initialize()
    print(f"✅ Loaded {await data_manager.count()} products")
    yield
    print("👋 Shutting down...")
    await data_manager.close()


app = FastAPI(
    title="E-commerce Product Data API",
    description="Real-time product data for price monitoring and competitive intelligence. MCP-ready for AI shopping agents.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Root & Health
@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "E-commerce Product Data API",
        "version": "1.0.0",
        "documentation": "/docs",
        "github": "https://github.com/francesca-tabor-ai/E-commerce-Product-Data-Aggregation-API"
    }


@app.get("/health", tags=["Health"])
async def health():
    total_products = await data_manager.count()
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "total_products": total_products
    }


# Product Endpoints
@app.get("/api/v1/products/search", response_model=ProductSearchResponse, tags=["Products"])
async def search_products(
    q: Optional[str] = Query(None, description="Search term"),
    category: Optional[ProductCategory] = None,
    brand: Optional[str] = None,
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    min_rating: Optional[float] = Query(None, ge=0, le=5),
    in_stock_only: bool = False,
    sort_by: str = Query("relevance", pattern="^(relevance|price_asc|price_desc|rating|newest)$"),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    Search for products with filters
    
    **Example:**
    `/api/v1/products/search?q=laptop&category=Computers&min_price=500&max_price=2000&sort_by=price_asc`
    """
    filters = {
        "q": q,
        "category": category,
        "brand": brand,
        "min_price": min_price,
        "max_price": max_price,
        "min_rating": min_rating,
        "in_stock_only": in_stock_only,
        "sort_by": sort_by
    }
    
    filters = {k: v for k, v in filters.items() if v is not None}
    
    results = await data_manager.search(filters, limit=limit, offset=offset)
    total = await data_manager.count_filtered(filters)
    
    return ProductSearchResponse(
        total=total,
        limit=limit,
        offset=offset,
        results=results
    )


@app.get("/api/v1/products/{product_id}", response_model=Product, tags=["Products"])
async def get_product(product_id: str):
    """Get detailed product information"""
    product = await data_manager.get_by_id(product_id)
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product '{product_id}' not found"
        )
    
    return product


@app.get("/api/v1/products/category/{category}", response_model=List[Product], tags=["Products"])
async def get_products_by_category(
    category: ProductCategory,
    limit: int = Query(20, ge=1, le=100)
):
    """Get products by category"""
    results = await data_manager.get_by_category(category, limit=limit)
    return results


# Price Tracking
@app.get("/api/v1/products/{product_id}/price-history", tags=["Price Tracking"])
async def get_price_history(
    product_id: str,
    days: int = Query(30, ge=1, le=365)
):
    """Get price history for a product"""
    product = await data_manager.get_by_id(product_id)
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    history = await data_manager.get_price_history(product_id, days=days)
    
    return {
        "product_id": product_id,
        "product_name": product.name,
        "current_price": product.current_price,
        "currency": product.currency,
        "history": [
            {
                "date": pp.date.isoformat(),
                "price": pp.price,
                "source": pp.source
            }
            for pp in history
        ],
        "days": days
    }


# Product Comparison
@app.post("/api/v1/products/compare", tags=["Advanced"])
async def compare_products(product_ids: List[str]):
    """Compare multiple products side-by-side"""
    if len(product_ids) < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 products to compare")
    
    if len(product_ids) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 products for comparison")
    
    products = []
    for pid in product_ids:
        product = await data_manager.get_by_id(pid)
        if product:
            products.append(product)
    
    if not products:
        raise HTTPException(status_code=404, detail="None of the products found")
    
    return {
        "total_compared": len(products),
        "products": products
    }


# Review Sentiment
@app.get("/api/v1/products/{product_id}/reviews/sentiment", tags=["Reviews"])
async def get_review_sentiment(product_id: str):
    """Get review sentiment analysis for a product"""
    product = await data_manager.get_by_id(product_id)
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    if not product.reviews_sentiment:
        raise HTTPException(
            status_code=404,
            detail="No review sentiment data available for this product"
        )
    
    return product.reviews_sentiment


# Statistics
@app.get("/api/v1/stats/overview", tags=["Statistics"])
async def get_stats():
    """Get API statistics"""
    total = await data_manager.count()
    categories = await data_manager.get_category_distribution()
    price_stats = await data_manager.get_price_stats()
    
    return {
        "total_products": total,
        "categories": categories,
        "price_stats": price_stats,
        "last_updated": datetime.utcnow()
    }


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", 8000))
    
    print(f"🚀 Starting E-commerce Product API on http://{host}:{port}")
    print(f"📚 Documentation: http://{host}:{port}/docs")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )
