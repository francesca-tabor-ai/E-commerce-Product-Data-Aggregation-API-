"""
Run All Scrapers
Orchestrates all product scrapers and updates database
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.scrapers.amazon_scraper import AmazonScraper
from src.utils.data_manager import DataManager
from src.utils.sentiment_analyzer import analyze_product_reviews


async def run_all_scrapers():
    """Run all enabled scrapers"""
    
    print("=" * 60)
    print("🛒 E-commerce Product Data API - Scraper")
    print("=" * 60)
    print(f"Started: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC\n")
    
    # Initialize data manager
    data_manager = DataManager()
    await data_manager.initialize()
    
    initial_count = await data_manager.count()
    print(f"📊 Current database: {initial_count} products\n")
    
    all_products = []
    
    # Run Amazon Scraper
    print("🔍 Running Amazon scraper...")
    try:
        amazon_scraper = AmazonScraper(delay_min=3, delay_max=6)
        
        # Search for different product categories
        search_terms = [
            "laptop",
            "wireless headphones",
            "smart watch",
            "kindle",
            "camera"
        ]
        
        for term in search_terms:
            print(f"\n  Searching: {term}")
            products = amazon_scraper.search_products(term, limit=10)
            all_products.extend(products)
            print(f"  Found: {len(products)} products")
        
        print(f"\n✅ Amazon: Total {len(all_products)} products scraped")
    
    except Exception as e:
        print(f"❌ Amazon scraper failed: {e}")
    
    # Process scraped data
    print(f"\n📊 Processing {len(all_products)} products...")
    
    if not all_products:
        print("⚠️  No products scraped")
        return
    
    # Remove duplicates
    unique_products = {}
    for product in all_products:
        if product.id not in unique_products:
            unique_products[product.id] = product
    
    unique_list = list(unique_products.values())
    print(f"✅ Unique products: {len(unique_list)}")
    
    # Update database
    print("\n💾 Updating database...")
    
    new_added = 0
    updated = 0
    
    for product in unique_list:
        existing = await data_manager.get_by_id(product.id)
        
        if not existing:
            await data_manager.add(product)
            new_added += 1
            print(f"  ➕ Added: {product.name[:50]}")
        else:
            # Update price history
            if product.current_price != existing.current_price:
                await data_manager.add_price_point(
                    product.id,
                    product.current_price,
                    "Amazon"
                )
            
            existing.last_updated = datetime.utcnow()
            existing.availability = product.availability
            await data_manager.update(existing)
            updated += 1
    
    final_count = await data_manager.count()
    
    # Final statistics
    print("\n" + "=" * 60)
    print("📊 Scraper Run Summary")
    print("=" * 60)
    print(f"Initial products:  {initial_count}")
    print(f"New products:      {new_added}")
    print(f"Updated products:  {updated}")
    print(f"Final products:    {final_count}")
    print(f"Net change:        +{final_count - initial_count}")
    print("=" * 60)
    print(f"Completed: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print("✅ Scraper completed!\n")
    
    await data_manager.close()


if __name__ == "__main__":
    asyncio.run(run_all_scrapers())
