"""
Amazon Product Scraper
Scrapes product data from Amazon (public data only)
FREE - Uses web scraping (no API key needed for basic data)
"""

import requests
from bs4 import BeautifulSoup
import time
import random
from datetime import datetime
from typing import List, Optional
import re

from src.models.product import (
    Product,
    ProductCategory,
    Availability,
    StockLevel,
    Ratings,
    ProductSource,
    Currency
)


class AmazonScraper:
    """Scrape product data from Amazon"""
    
    BASE_URL = "https://www.amazon.com"
    
    def __init__(self, delay_min=3, delay_max=6):
        """
        Initialize scraper
        
        Args:
            delay_min: Minimum delay between requests (seconds)
            delay_max: Maximum delay between requests (seconds)
        """
        self.delay_min = delay_min
        self.delay_max = delay_max
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept': 'text/html,application/xhtml+xml',
        })
    
    def _delay(self):
        """Random delay to be respectful"""
        time.sleep(random.uniform(self.delay_min, self.delay_max))
    
    def search_products(
        self,
        query: str,
        category: str = None,
        limit: int = 20
    ) -> List[Product]:
        """
        Search for products on Amazon
        
        Args:
            query: Search term
            category: Product category
            limit: Maximum products to scrape
            
        Returns:
            List of Product objects
        """
        products = []
        
        print(f"🔍 Searching Amazon for: {query}")
        
        try:
            # Build search URL
            search_url = f"{self.BASE_URL}/s?k={query.replace(' ', '+')}"
            if category:
                search_url += f"&i={category}"
            
            response = self.session.get(search_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find product cards
            # Note: Amazon's HTML structure changes frequently
            # This is a simplified version - production would need more robust selectors
            product_cards = soup.find_all('div', {'data-component-type': 's-search-result'})[:limit]
            
            for card in product_cards:
                try:
                    product = self._parse_product_card(card)
                    if product:
                        products.append(product)
                        print(f"  ✅ Found: {product.name[:50]}...")
                        self._delay()
                
                except Exception as e:
                    print(f"  ⚠️  Error parsing product: {e}")
                    continue
        
        except Exception as e:
            print(f"  ❌ Search failed: {e}")
        
        return products
    
    def _parse_product_card(self, card) -> Optional[Product]:
        """Parse Amazon product card HTML"""
        try:
            # Extract ASIN (Amazon Standard Identification Number)
            asin = card.get('data-asin')
            if not asin:
                return None
            
            # Extract name
            name_elem = card.find('h2')
            if not name_elem:
                return None
            name = name_elem.text.strip()
            
            # Extract price
            price_elem = card.find('span', {'class': 'a-price'})
            if price_elem:
                price_whole = price_elem.find('span', {'class': 'a-price-whole'})
                price_fraction = price_elem.find('span', {'class': 'a-price-fraction'})
                
                if price_whole:
                    price_str = price_whole.text.replace(',', '').replace('$', '')
                    if price_fraction:
                        price_str += price_fraction.text
                    
                    try:
                        current_price = float(price_str)
                    except:
                        current_price = 0.0
                else:
                    current_price = 0.0
            else:
                current_price = 0.0
            
            # Extract rating
            rating_elem = card.find('span', {'class': 'a-icon-alt'})
            if rating_elem:
                rating_text = rating_elem.text
                rating_match = re.search(r'([\d.]+) out of', rating_text)
                if rating_match:
                    rating = float(rating_match.group(1))
                else:
                    rating = 0.0
            else:
                rating = 0.0
            
            # Extract review count
            review_elem = card.find('span', {'class': 'a-size-base'})
            if review_elem:
                review_text = review_elem.text.replace(',', '')
                review_match = re.search(r'(\d+)', review_text)
                if review_match:
                    review_count = int(review_match.group(1))
                else:
                    review_count = 0
            else:
                review_count = 0
            
            # Extract image
            img_elem = card.find('img', {'class': 's-image'})
            image_url = img_elem.get('src') if img_elem else None
            
            # Extract product URL
            link_elem = card.find('a', {'class': 'a-link-normal'})
            product_url = f"{self.BASE_URL}{link_elem.get('href')}" if link_elem else None
            
            # Determine category (simplified)
            category = self._determine_category(name)
            
            # Create product ID
            product_id = f"prod_amz_{asin}"
            
            # Create availability
            availability = Availability(
                in_stock=current_price > 0,
                stock_level=StockLevel.IN_STOCK if current_price > 0 else StockLevel.OUT_OF_STOCK,
                shipping_time="Varies"
            )
            
            # Create ratings
            ratings = None
            if rating > 0:
                ratings = Ratings(
                    average=rating,
                    count=review_count
                )
            
            # Create source
            source = ProductSource(
                name="Amazon",
                url=product_url,
                price=current_price,
                availability=availability,
                last_checked=datetime.utcnow()
            )
            
            # Create product
            product = Product(
                id=product_id,
                name=name,
                slug=name.lower().replace(' ', '-')[:50],
                category=category,
                brand=None,  # Would need to extract from product page
                current_price=current_price,
                currency=Currency.USD,
                availability=availability,
                ratings=ratings,
                images=[image_url] if image_url else [],
                asin=asin,
                sources=[source],
                first_seen=datetime.utcnow(),
                last_updated=datetime.utcnow(),
                data_quality_score=40  # Low score for basic scraping
            )
            
            return product
        
        except Exception as e:
            print(f"Error parsing card: {e}")
            return None
    
    def _determine_category(self, name: str) -> ProductCategory:
        """Determine product category from name"""
        name_lower = name.lower()
        
        # Simple keyword matching
        if any(word in name_lower for word in ['laptop', 'computer', 'macbook', 'pc']):
            return ProductCategory.COMPUTERS
        elif any(word in name_lower for word in ['phone', 'iphone', 'android', 'samsung']):
            return ProductCategory.SMARTPHONES
        elif any(word in name_lower for word in ['book', 'novel', 'kindle']):
            return ProductCategory.BOOKS
        elif any(word in name_lower for word in ['clothes', 'shirt', 'pants', 'dress', 'fashion']):
            return ProductCategory.FASHION
        elif any(word in name_lower for word in ['toy', 'game', 'lego', 'doll']):
            return ProductCategory.TOYS
        elif any(word in name_lower for word in ['kitchen', 'home', 'furniture', 'decor']):
            return ProductCategory.HOME
        else:
            return ProductCategory.ELECTRONICS


# CLI for testing
if __name__ == "__main__":
    print("🛒 Amazon Product Scraper")
    print("=" * 50)
    
    scraper = AmazonScraper()
    
    # Test search
    products = scraper.search_products("laptop", limit=5)
    
    print(f"\n✅ Scraped {len(products)} products from Amazon")
    
    for i, product in enumerate(products, 1):
        print(f"\n{i}. {product.name[:60]}")
        print(f"   Price: ${product.current_price:.2f}")
        print(f"   Category: {product.category.value}")
        if product.ratings:
            print(f"   Rating: {product.ratings.average}/5 ({product.ratings.count} reviews)")
        print(f"   ASIN: {product.asin}")
    
    # Save to JSON
    import json
    from pathlib import Path
    
    output_file = Path("src/data/amazon_scraped.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    data = [product.model_dump(mode='json') for product in products]
    
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2, default=str)
    
    print(f"\n💾 Saved to {output_file}")
