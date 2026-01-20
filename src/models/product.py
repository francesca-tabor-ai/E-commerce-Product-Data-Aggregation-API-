"""
Data models for E-commerce Product Data Aggregation API
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, HttpUrl, Field, field_validator
from enum import Enum


class ProductCategory(str, Enum):
    """Product categories"""
    ELECTRONICS = "Electronics"
    COMPUTERS = "Computers & Laptops"
    SMARTPHONES = "Smartphones"
    HOME = "Home & Kitchen"
    FASHION = "Fashion & Apparel"
    BEAUTY = "Beauty & Personal Care"
    SPORTS = "Sports & Outdoors"
    BOOKS = "Books"
    TOYS = "Toys & Games"
    AUTOMOTIVE = "Automotive"
    GROCERIES = "Groceries & Food"
    HEALTH = "Health & Wellness"
    FURNITURE = "Furniture"
    JEWELRY = "Jewelry"
    OTHER = "Other"


class StockLevel(str, Enum):
    """Stock availability levels"""
    OUT_OF_STOCK = "Out of Stock"
    LOW = "Low Stock"
    MEDIUM = "Medium Stock"
    HIGH = "High Stock"
    IN_STOCK = "In Stock"
    UNKNOWN = "Unknown"


class Currency(str, Enum):
    """Supported currencies"""
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    JPY = "JPY"
    CAD = "CAD"
    AUD = "AUD"


class PricePoint(BaseModel):
    """Historical price point"""
    date: datetime
    price: float
    currency: Currency = Currency.USD
    source: str


class Availability(BaseModel):
    """Product availability info"""
    in_stock: bool
    stock_level: StockLevel = StockLevel.UNKNOWN
    shipping_time: Optional[str] = None  # e.g., "1-2 days"
    fulfillment_by: Optional[str] = None  # e.g., "Amazon", "Seller"


class RatingDistribution(BaseModel):
    """Star rating distribution"""
    five_star: int = Field(ge=0, le=100)
    four_star: int = Field(ge=0, le=100)
    three_star: int = Field(ge=0, le=100)
    two_star: int = Field(ge=0, le=100)
    one_star: int = Field(ge=0, le=100)


class Ratings(BaseModel):
    """Product ratings"""
    average: float = Field(ge=0, le=5)
    count: int = Field(ge=0)
    distribution: Optional[RatingDistribution] = None


class ReviewSentiment(BaseModel):
    """Review sentiment analysis"""
    positive: int = Field(ge=0, le=100, description="Positive sentiment %")
    neutral: int = Field(ge=0, le=100, description="Neutral sentiment %")
    negative: int = Field(ge=0, le=100, description="Negative sentiment %")
    top_pros: List[str] = Field(default_factory=list, max_length=10)
    top_cons: List[str] = Field(default_factory=list, max_length=10)
    sample_reviews: List[str] = Field(default_factory=list, max_length=5)


class ProductSource(BaseModel):
    """Data source for product"""
    name: str  # e.g., "Amazon", "Walmart"
    url: HttpUrl
    price: Optional[float] = None
    availability: Optional[Availability] = None
    last_checked: datetime = Field(default_factory=datetime.utcnow)


class Product(BaseModel):
    """Complete product model"""
    # Core identifiers
    id: str = Field(..., description="Unique product ID")
    name: str = Field(..., min_length=1, max_length=500)
    slug: Optional[str] = None
    
    # Classification
    category: ProductCategory
    subcategory: Optional[str] = None
    brand: Optional[str] = None
    manufacturer: Optional[str] = None
    
    # Pricing
    current_price: float = Field(ge=0)
    currency: Currency = Currency.USD
    original_price: Optional[float] = Field(None, ge=0)  # MSRP
    discount_percentage: Optional[float] = Field(None, ge=0, le=100)
    price_history: List[PricePoint] = Field(default_factory=list)
    
    # Availability
    availability: Availability
    
    # Ratings & Reviews
    ratings: Optional[Ratings] = None
    reviews_sentiment: Optional[ReviewSentiment] = None
    
    # Product Details
    description: Optional[str] = Field(None, max_length=5000)
    specifications: Dict[str, Any] = Field(default_factory=dict)
    features: List[str] = Field(default_factory=list)
    
    # Media
    images: List[HttpUrl] = Field(default_factory=list)
    video_url: Optional[HttpUrl] = None
    
    # Identification
    sku: Optional[str] = None
    upc: Optional[str] = None
    ean: Optional[str] = None
    asin: Optional[str] = None  # Amazon Standard Identification Number
    
    # SEO
    tags: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    
    # Data sources
    sources: List[ProductSource] = Field(default_factory=list)
    
    # Metadata
    first_seen: datetime = Field(default_factory=datetime.utcnow)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    data_quality_score: int = Field(50, ge=0, le=100)
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "prod_12345",
                "name": "Apple MacBook Pro 16-inch",
                "category": "Computers & Laptops",
                "brand": "Apple",
                "current_price": 2499.99,
                "currency": "USD",
                "availability": {
                    "in_stock": True,
                    "stock_level": "High Stock",
                    "shipping_time": "1-2 days"
                },
                "ratings": {
                    "average": 4.7,
                    "count": 2543
                }
            }
        }


class ProductSearchQuery(BaseModel):
    """Search query parameters"""
    q: Optional[str] = None
    category: Optional[ProductCategory] = None
    brand: Optional[str] = None
    min_price: Optional[float] = Field(None, ge=0)
    max_price: Optional[float] = Field(None, ge=0)
    min_rating: Optional[float] = Field(None, ge=0, le=5)
    in_stock_only: bool = False
    sort_by: str = Field("relevance", pattern="^(relevance|price_asc|price_desc|rating|newest)$")
    limit: int = Field(10, ge=1, le=100)
    offset: int = Field(0, ge=0)


class ProductSearchResponse(BaseModel):
    """Search response"""
    total: int
    limit: int
    offset: int
    results: List[Product]


class PriceAlert(BaseModel):
    """Price alert configuration"""
    id: str
    product_id: str
    target_price: float = Field(gt=0)
    currency: Currency = Currency.USD
    email: str
    active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    triggered_at: Optional[datetime] = None
