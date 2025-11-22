"""
Vastr Fashion Intelligence Platform
Automated Data Sync & Update System

Features:
- Incremental updates (only fetch changed products)
- Track price changes over time
- Detect new products and removed products
- Schedule periodic syncs
- Maintain data freshness
"""

from pymongo import MongoClient
import requests
import time
from datetime import datetime, timedelta
from typing import Dict, List, Set
import json
import schedule

# ============================================
# CONFIGURATION
# ============================================
MONGO_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "vastr_fashion_db"

BRANDS = {
    'nishat': {
        'name': 'Nishat Linen',
        'base_url': 'https://nishatlinen.com',
        'collections':[
    # Main collections
    'new-in-unstitched',  # New arrivals unstitched
    'unstitched',  # Unstitched
    'ready-to-wear-1',  # Ready to wear
    'ready-to-stitch',  # Ready to stitch
    'luxury',
    'pret',
    'bottoms',# Luxury pret (assuming handle; adjust if needed)
    'freedom-to-buy',  # Freedom to buy
    'sale',  # Sale (common handle)
]

    },
    'ethnic': {
        'name': 'Ethnic',
        'base_url': 'https://pk.ethnc.com',
        'collections': ['new-arrivals', 'rozana', 'casual','luxury','unstitched','special-price','western','studio','basics']
    },
    'gulahmed': {
        'name': 'Gul Ahmed',
        'base_url': 'https://www.gulahmedshop.com',
        'collections': [
    'women',  # Main women's collection
    'unstitched-fabric',  # Unstitched fabrics
    'women-ideas-pret-signature',  # Ready-to-wear signature
    'women-ideas-pret-essentials',  # Pret essentials
    'women-ideas-pret-everyday-edit',  # Everyday edit
    'women-ideas-pret-9-to-5',  # Workwear
    'salt-western-wear-women',  # Western wear
    'women-unstitched-to-stitched',  # Unstitched to stitched
]
    },
    'generation': {
        'name': 'Generation',
        'base_url': 'https://www.generation.com.pk',
        'collections': ['new-ins', 'annual-winter-sale', 'annual-summer-sale','formals','sale','khaddar-collection','luxury-pret','hand-crafted-2-piece']
    },
    'crossstitch': {
        'name': 'Cross Stitch',
        'base_url': 'https://www.crossstitch.pk',
        'collections': ['lawn', 'ready-to-wear','luxury-pret','sale','winter','embroidered','new-arrivals','premium-lawn','luxe-atelier','basic-pret','bottoms','exclusive-pret']
    },
    'mariab': {
        'name': 'Maria B',
        'base_url': 'https://www.mariab.pk',
        'collections': [
    'lawn-collection',  # Unstitched lawn/summer
    'ready-to-wear',    # Ready-to-wear/pret
    'luxury-pret',      # Luxury pret
    'bridal',           # Bridal/formals
    'sale',             # Sale items
    'embroidered',
    'new-in',
    'luxury-formals',
    'silk-prints',
    'm.statement',
    'm.prints',
    'lawn',
    'chiffon',
    'mbroidered',
    'unstitched-chiffon','formals','signature', 'linen'
]
    },
    'limelight': {
        'name': 'Limelight',
        'base_url': 'https://limelight.pk',
        'collections': [
    'unstitched-winter',  # Winter unstitched
    'pret',  # Pret
    'unstitched',  # Unstitched
    'signature',  # Signature
    'unstitched-lawn',  # Lawn unstitched
    'pret-special-price',
    'ready to wear',
    'co-ords',
    'western'# Special price pret
]
    }
}

SYNC_INTERVAL_HOURS = 6  # Sync every 6 hours
DELAY_BETWEEN_REQUESTS = 2  # seconds


# ============================================
# DATA SYNC MANAGER
# ============================================
class VastrDataSync:
    """
    Manages automated data synchronization
    """

    def __init__(self):
        """Initialize sync manager"""
        self.client = MongoClient(MONGO_URI)
        self.db = self.client[DATABASE_NAME]

        # Collections
        self.products = self.db['products']
        self.brands = self.db['brands']
        self.price_history = self.db['price_history']
        self.sync_logs = self.db['sync_logs']
        self.removed_products = self.db['removed_products']

        print("✅ Data Sync Manager initialized")

    def fetch_live_products(self, brand_id: str, collection: str) -> List[Dict]:
        """
        Fetch current products from brand's Shopify API
        """
        brand_config = BRANDS[brand_id]
        base_url = brand_config['base_url']
        all_products = []
        page = 1
        max_pages = 50

        while page <= max_pages:
            url = f"{base_url}/collections/{collection}/products.json?page={page}&limit=250"

            try:
                response = requests.get(url, timeout=10)

                if response.status_code != 200:
                    break

                data = response.json()
                products = data.get('products', [])

                if not products:
                    break

                all_products.extend(products)
                page += 1
                time.sleep(DELAY_BETWEEN_REQUESTS)

            except Exception as e:
                print(f"   ⚠️ Error fetching {brand_id}/{collection}: {e}")
                break

        return all_products

    def sync_brand(self, brand_id: str) -> Dict:
        """
        Sync a single brand's data
        Returns sync statistics
        """
        brand_config = BRANDS[brand_id]
        brand_name = brand_config['name']

        print(f"\n{'=' * 60}")
        print(f"Syncing: {brand_name}")
        print(f"{'=' * 60}")

        stats = {
            'brand_id': brand_id,
            'brand_name': brand_name,
            'new_products': 0,
            'updated_products': 0,
            'price_changes': 0,
            'removed_products': 0,
            'errors': 0,
            'start_time': datetime.now()
        }

        # Get existing product IDs from database
        existing_products = self.products.find({'brand_id': brand_id})
        existing_ids = {str(p['product_id']) for p in existing_products}

        # Fetch live products
        live_products = []
        for collection in brand_config['collections']:
            print(f"   📦 Fetching collection: {collection}")
            products = self.fetch_live_products(brand_id, collection)
            live_products.extend(products)

        # Deduplicate
        live_products_map = {str(p['id']): p for p in live_products}
        live_ids = set(live_products_map.keys())

        print(f"\n   📊 Comparison:")
        print(f"      Existing in DB: {len(existing_ids)}")
        print(f"      Live on website: {len(live_ids)}")

        # Detect changes
        new_ids = live_ids - existing_ids
        removed_ids = existing_ids - live_ids
        common_ids = existing_ids & live_ids

        print(f"      New products: {len(new_ids)}")
        print(f"      Removed products: {len(removed_ids)}")
        print(f"      To check for updates: {len(common_ids)}")

        # Process new products
        for product_id in new_ids:
            try:
                live_product = live_products_map[product_id]
                parsed = self._parse_product(live_product, brand_id, brand_name)

                self.products.insert_one(parsed)
                stats['new_products'] += 1

                # Log price
                if parsed.get('price_min'):
                    self._log_price(product_id, brand_id, parsed['price_min'])

            except Exception as e:
                print(f"   ❌ Error adding new product {product_id}: {e}")
                stats['errors'] += 1

        # Process removed products
        for product_id in removed_ids:
            try:
                # Move to removed_products collection
                product = self.products.find_one({
                    'product_id': product_id,
                    'brand_id': brand_id
                })

                if product:
                    product['removed_at'] = datetime.now()
                    self.removed_products.insert_one(product)

                    # Delete from main products
                    self.products.delete_one({
                        'product_id': product_id,
                        'brand_id': brand_id
                    })

                    stats['removed_products'] += 1

            except Exception as e:
                print(f"   ❌ Error removing product {product_id}: {e}")
                stats['errors'] += 1

        # Process updated products
        for product_id in common_ids:
            try:
                live_product = live_products_map[product_id]
                parsed = self._parse_product(live_product, brand_id, brand_name)

                # Get existing product
                existing = self.products.find_one({
                    'product_id': product_id,
                    'brand_id': brand_id
                })

                # Check for price change
                old_price = existing.get('price_min', 0)
                new_price = parsed.get('price_min', 0)

                if old_price != new_price and new_price > 0:
                    stats['price_changes'] += 1
                    self._log_price(product_id, brand_id, new_price, old_price)
                    print(f"   💰 Price change: {product_id} - PKR {old_price:,.0f} → PKR {new_price:,.0f}")

                # Update product
                parsed['last_updated'] = datetime.now()
                parsed['scraped_at'] = existing.get('scraped_at')  # Keep original scrape date

                self.products.update_one(
                    {'product_id': product_id, 'brand_id': brand_id},
                    {'$set': parsed}
                )

                stats['updated_products'] += 1

            except Exception as e:
                print(f"   ❌ Error updating product {product_id}: {e}")
                stats['errors'] += 1

        # Update brand stats
        stats['end_time'] = datetime.now()
        stats['duration_seconds'] = (stats['end_time'] - stats['start_time']).total_seconds()

        self._update_brand_metadata(brand_id, stats)
        self._log_sync(stats)

        # Print summary
        print(f"\n   ✅ Sync Complete:")
        print(f"      New: {stats['new_products']}")
        print(f"      Updated: {stats['updated_products']}")
        print(f"      Price changes: {stats['price_changes']}")
        print(f"      Removed: {stats['removed_products']}")
        print(f"      Errors: {stats['errors']}")
        print(f"      Duration: {stats['duration_seconds']:.1f}s")

        return stats

    def sync_all_brands(self) -> Dict:
        """
        Sync all brands
        """
        print("""
    ╔═══════════════════════════════════════════════════════╗
    ║                                                       ║
    ║            VASTR DATA SYNC STARTING                   ║
    ║                                                       ║
    ╚═══════════════════════════════════════════════════════╝
        """)

        overall_stats = {
            'start_time': datetime.now(),
            'brands_synced': 0,
            'total_new': 0,
            'total_updated': 0,
            'total_price_changes': 0,
            'total_removed': 0,
            'total_errors': 0
        }

        for brand_id in BRANDS.keys():
            try:
                stats = self.sync_brand(brand_id)

                overall_stats['brands_synced'] += 1
                overall_stats['total_new'] += stats['new_products']
                overall_stats['total_updated'] += stats['updated_products']
                overall_stats['total_price_changes'] += stats['price_changes']
                overall_stats['total_removed'] += stats['removed_products']
                overall_stats['total_errors'] += stats['errors']

                # Delay between brands
                time.sleep(3)

            except Exception as e:
                print(f"\n❌ Failed to sync {brand_id}: {e}")
                overall_stats['total_errors'] += 1

        overall_stats['end_time'] = datetime.now()
        overall_stats['total_duration'] = (overall_stats['end_time'] - overall_stats['start_time']).total_seconds()

        # Print overall summary
        print(f"\n{'=' * 60}")
        print("SYNC COMPLETE - OVERALL SUMMARY")
        print(f"{'=' * 60}")
        print(f"Brands synced: {overall_stats['brands_synced']}/{len(BRANDS)}")
        print(f"Total new products: {overall_stats['total_new']}")
        print(f"Total updated: {overall_stats['total_updated']}")
        print(f"Total price changes: {overall_stats['total_price_changes']}")
        print(f"Total removed: {overall_stats['total_removed']}")
        print(f"Total errors: {overall_stats['total_errors']}")
        print(f"Total duration: {overall_stats['total_duration'] / 60:.1f} minutes")

        return overall_stats

    def _parse_product(self, product: Dict, brand_id: str, brand_name: str) -> Dict:
        """Parse Shopify product to standard format"""

        # Handle tags - can be string or list
        tags = product.get('tags', [])
        if isinstance(tags, str):
            tags = tags.split(', ') if tags else []
        elif not isinstance(tags, list):
            tags = []

        parsed = {
            'product_id': str(product.get('id')),
            'brand_id': brand_id,
            'brand_name': brand_name,
            'title': product.get('title'),
            'handle': product.get('handle'),
            'vendor': product.get('vendor'),
            'product_type': product.get('product_type'),
            'created_at': product.get('created_at'),
            'updated_at': product.get('updated_at'),
            'published_at': product.get('published_at'),
            'tags': tags,
            'url': f"{BRANDS[brand_id]['base_url']}/products/{product.get('handle')}",
            'description': product.get('body_html', ''),
            'variants': [],
            'images': [],
            'last_updated': datetime.now()
        }

        # Variants
        for variant in product.get('variants', []):
            parsed['variants'].append({
                'id': variant.get('id'),
                'title': variant.get('title'),
                'price': float(variant.get('price', 0)),
                'compare_at_price': float(variant.get('compare_at_price', 0)) if variant.get(
                    'compare_at_price') else None,
                'sku': variant.get('sku'),
                'available': variant.get('available'),
                'inventory_quantity': variant.get('inventory_quantity', 0),
            })

        # Images
        for img in product.get('images', []):
            parsed['images'].append({
                'id': img.get('id'),
                'src': img.get('src'),
                'alt': img.get('alt'),
            })

        # Price range
        prices = [v['price'] for v in parsed['variants'] if v.get('price')]
        if prices:
            parsed['price_min'] = min(prices)
            parsed['price_max'] = max(prices)
            parsed['currency'] = 'PKR'

        # Availability
        parsed['available'] = any(v.get('available') for v in parsed['variants'])

        return parsed

    def _log_price(self, product_id: str, brand_id: str, new_price: float, old_price: float = None):
        """Log price change"""
        price_entry = {
            'product_id': product_id,
            'brand_id': brand_id,
            'price': new_price,
            'old_price': old_price,
            'date': datetime.now(),
            'change_detected': old_price is not None
        }

        self.price_history.insert_one(price_entry)

    def _update_brand_metadata(self, brand_id: str, stats: Dict):
        """Update brand document"""
        product_count = self.products.count_documents({'brand_id': brand_id})

        self.brands.update_one(
            {'brand_id': brand_id},
            {
                '$set': {
                    'product_count': product_count,
                    'last_synced': datetime.now(),
                    'last_sync_stats': {
                        'new': stats['new_products'],
                        'updated': stats['updated_products'],
                        'price_changes': stats['price_changes'],
                        'removed': stats['removed_products']
                    }
                }
            }
        )

    def _log_sync(self, stats: Dict):
        """Log sync activity"""
        self.sync_logs.insert_one(stats)

    def get_last_sync_time(self, brand_id: str = None) -> datetime:
        """Get last sync time for a brand or all brands"""
        if brand_id:
            brand = self.brands.find_one({'brand_id': brand_id})
            return brand.get('last_synced') if brand else None
        else:
            # Get oldest last_synced across all brands
            brands = list(self.brands.find())
            sync_times = [b.get('last_synced') for b in brands if b.get('last_synced')]
            return min(sync_times) if sync_times else None

    def close(self):
        """Close database connection"""
        self.client.close()


# ============================================
# SCHEDULER
# ============================================
def run_scheduled_sync():
    """Run scheduled data sync"""
    sync_manager = VastrDataSync()
    sync_manager.sync_all_brands()
    sync_manager.close()


def setup_scheduler():
    """Setup automatic sync schedule"""
    print(f"📅 Scheduling automatic sync every {SYNC_INTERVAL_HOURS} hours")

    # Schedule sync
    schedule.every(SYNC_INTERVAL_HOURS).hours.do(run_scheduled_sync)

    # Also schedule daily sync at 3 AM
    schedule.every().day.at("03:00").do(run_scheduled_sync)

    print("✅ Scheduler configured")
    print(f"   - Every {SYNC_INTERVAL_HOURS} hours")
    print(f"   - Daily at 3:00 AM")

    # Run scheduler
    print("\n⏰ Scheduler running... (Press Ctrl+C to stop)")
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute


# ============================================
# MAIN EXECUTION
# ============================================
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--schedule":
        # Run with scheduler
        setup_scheduler()
    else:
        # Run manual sync once
        sync_manager = VastrDataSync()
        sync_manager.sync_all_brands()
        sync_manager.close()

        print("\n💡 To run automatic scheduled syncs:")
        print("   python vastr_data_sync.py --schedule")