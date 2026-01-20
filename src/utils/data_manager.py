"""
Data Manager for E-commerce Product Data API
Handles JSON-based storage (free!) - upgradable to PostgreSQL
"""

import json
import os
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from pathlib import Path

from src.models.product import Product, ProductCategory, PricePoint


class DataManager:
    """Manages product data using JSON file storage"""
    
    def __init__(self, data_file: str = None):
        if data_file is None:
            data_file = os.getenv("JSON_DATA_PATH", "src/data/products.json")
        
        self.data_file = Path(data_file)
        self.products: Dict[str, Product] = {}
        self._ensure_data_dir()
    
    def _ensure_data_dir(self):
        """Create data directory if it doesn't exist"""
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        
        if not self.data_file.exists():
            with open(self.data_file, 'w') as f:
                json.dump([], f)
    
    async def initialize(self):
        """Load data from JSON file"""
        try:
            with open(self.data_file, 'r') as f:
                data = json.load(f)
            
            self.products = {}
            for item in data:
                try:
                    product = Product(**item)
                    self.products[product.id] = product
                except Exception as e:
                    print(f"Warning: Failed to load product: {e}")
                    continue
            
            print(f"✅ Loaded {len(self.products)} products from {self.data_file}")
        
        except (json.JSONDecodeError, FileNotFoundError):
            print(f"⚠️  Starting with empty dataset")
            self.products = {}
    
    async def save(self):
        """Save data to JSON file"""
        data = [product.model_dump(mode='json') for product in self.products.values()]
        
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        print(f"💾 Saved {len(data)} products")
    
    async def close(self):
        """Save and cleanup"""
        await self.save()
    
    # CRUD Operations
    
    async def add(self, product: Product) -> Product:
        """Add a new product"""
        self.products[product.id] = product
        await self.save()
        return product
    
    async def update(self, product: Product) -> Product:
        """Update an existing product"""
        product.last_updated = datetime.utcnow()
        self.products[product.id] = product
        await self.save()
        return product
    
    async def delete(self, product_id: str) -> bool:
        """Delete a product"""
        if product_id in self.products:
            del self.products[product_id]
            await self.save()
            return True
        return False
    
    async def get_by_id(self, product_id: str) -> Optional[Product]:
        """Get product by ID"""
        return self.products.get(product_id)
    
    async def count(self) -> int:
        """Get total number of products"""
        return len(self.products)
    
    # Search & Filter
    
    async def search(
        self,
        filters: Dict[str, Any],
        limit: int = 10,
        offset: int = 0
    ) -> List[Product]:
        """Search products with filters"""
        results = list(self.products.values())
        
        # Apply filters
        if "q" in filters and filters["q"]:
            query = filters["q"].lower()
            results = [
                p for p in results
                if query in p.name.lower()
                or (p.description and query in p.description.lower())
                or (p.brand and query in p.brand.lower())
                or any(query in tag.lower() for tag in p.tags)
            ]
        
        if "category" in filters:
            category = filters["category"]
            results = [p for p in results if p.category == category]
        
        if "brand" in filters and filters["brand"]:
            brand = filters["brand"].lower()
            results = [p for p in results if p.brand and brand in p.brand.lower()]
        
        if "min_price" in filters and filters["min_price"] is not None:
            min_price = filters["min_price"]
            results = [p for p in results if p.current_price >= min_price]
        
        if "max_price" in filters and filters["max_price"] is not None:
            max_price = filters["max_price"]
            results = [p for p in results if p.current_price <= max_price]
        
        if "min_rating" in filters and filters["min_rating"] is not None:
            min_rating = filters["min_rating"]
            results = [
                p for p in results
                if p.ratings and p.ratings.average >= min_rating
            ]
        
        if "in_stock_only" in filters and filters["in_stock_only"]:
            results = [p for p in results if p.availability.in_stock]
        
        # Sort
        sort_by = filters.get("sort_by", "relevance")
        if sort_by == "price_asc":
            results.sort(key=lambda p: p.current_price)
        elif sort_by == "price_desc":
            results.sort(key=lambda p: p.current_price, reverse=True)
        elif sort_by == "rating":
            results.sort(
                key=lambda p: p.ratings.average if p.ratings else 0,
                reverse=True
            )
        elif sort_by == "newest":
            results.sort(key=lambda p: p.first_seen, reverse=True)
        
        # Pagination
        return results[offset:offset + limit]
    
    async def count_filtered(self, filters: Dict[str, Any]) -> int:
        """Count products matching filters"""
        results = await self.search(filters, limit=999999, offset=0)
        return len(results)
    
    async def get_by_category(
        self,
        category: ProductCategory,
        limit: int = 20
    ) -> List[Product]:
        """Get products by category"""
        results = [p for p in self.products.values() if p.category == category]
        results.sort(
            key=lambda p: p.ratings.average if p.ratings else 0,
            reverse=True
        )
        return results[:limit]
    
    # Price Tracking
    
    async def add_price_point(self, product_id: str, price: float, source: str):
        """Add a price point to product history"""
        product = await self.get_by_id(product_id)
        if not product:
            return None
        
        price_point = PricePoint(
            date=datetime.utcnow(),
            price=price,
            currency=product.currency,
            source=source
        )
        
        product.price_history.append(price_point)
        product.last_updated = datetime.utcnow()
        
        await self.update(product)
        return product
    
    async def get_price_history(
        self,
        product_id: str,
        days: int = 30
    ) -> List[PricePoint]:
        """Get price history for a product"""
        product = await self.get_by_id(product_id)
        if not product:
            return []
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        return [
            pp for pp in product.price_history
            if pp.date >= cutoff_date
        ]
    
    # Bulk Operations
    
    async def add_many(self, products: List[Product]) -> int:
        """Add multiple products"""
        added = 0
        for product in products:
            if product.id not in self.products:
                self.products[product.id] = product
                added += 1
        
        await self.save()
        return added
    
    async def get_all(self) -> List[Product]:
        """Get all products"""
        return list(self.products.values())
    
    # Analytics
    
    async def get_category_distribution(self) -> Dict[str, int]:
        """Get count of products per category"""
        distribution = {}
        
        for product in self.products.values():
            cat_name = product.category.value if hasattr(product.category, 'value') else str(product.category)
            distribution[cat_name] = distribution.get(cat_name, 0) + 1
        
        return dict(sorted(distribution.items(), key=lambda x: x[1], reverse=True))
    
    async def get_price_stats(self) -> Dict[str, float]:
        """Get price statistics"""
        if not self.products:
            return {"min": 0, "max": 0, "average": 0, "median": 0}
        
        prices = [p.current_price for p in self.products.values()]
        prices.sort()
        
        return {
            "min": min(prices),
            "max": max(prices),
            "average": sum(prices) / len(prices),
            "median": prices[len(prices) // 2]
        }
