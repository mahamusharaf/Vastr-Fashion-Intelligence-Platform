from pymongo import MongoClient
from datetime import datetime
import json
import os
import glob

# ============================================
# CONFIGURATION
# ============================================

# MongoDB Connection String
MONGO_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "vastr_fashion_db"

# Data directory
DATA_DIR = "../data"

# Brand file mapping
BRAND_FILES = {
    'nishat': 'nishat_clothing_*.json',
    'ethnic': 'ethnic_clothing_*.json',
    'gulahmed': 'gulahmed_clothing_*.json',
    'generation': 'generation_clothing_*.json',
    'crossstitch': 'cross_stitch_clothing_*.json',
    'mariab': 'maria_b_clothing_*.json',
    'limelight': 'limelight_clothing_*.json',
    'sapphire': 'sapphire_clothing_*.json',
    'sanasafinaz': 'sana_safinaz_clothing_*.json'
}

# ============================================
# DATABASE CLASS
# ============================================
class VastrDatabase:
    """MongoDB Database Manager"""

    def __init__(self, connection_string=MONGO_URI, db_name=DATABASE_NAME):
        try:
            self.client = MongoClient(connection_string)
            self.db = self.client[db_name]
            self.products = self.db['products']
            self.brands = self.db['brands']
            self.price_history = self.db['price_history']
            self.scrape_logs = self.db['scrape_logs']
            print(f"✅ Connected to MongoDB: {db_name}")
        except Exception as e:
            print(f"❌ Failed to connect to MongoDB: {e}")
            exit(1)

    def insert_products_bulk(self, products_list, brand_id, brand_name):
        """Insert multiple products at once"""
        inserted = 0
        updated = 0
        errors = 0

        for product in products_list:
            try:
                # Ensure product_id is set
                if 'product_id' not in product:
                    if 'id' in product:
                        product['product_id'] = str(product['id'])
                    else:
                        print(f"   ⚠️ Skipping product with missing ID: {product.get('title', 'Unknown')}")
                        errors += 1
                        continue

                product['brand_id'] = brand_id
                product['brand_name'] = brand_name
                product['scraped_at'] = datetime.now()
                product['last_updated'] = datetime.now()

                result = self.products.update_one(
                    {
                        'product_id': product['product_id'],
                        'brand_id': brand_id
                    },
                    {'$set': product},
                    upsert=True
                )

                if result.upserted_id:
                    inserted += 1
                else:
                    updated += 1

                # Log price
                if 'price_min' in product:
                    self.log_price(
                        product['product_id'],
                        brand_id,
                        product['price_min'],
                        product.get('price_max')
                    )

            except Exception as e:
                errors += 1
                if errors <= 3:
                    print(f"   ❌ Error processing product {product.get('product_id', 'unknown')}: {e}")

        # Update brand stats
        self.update_brand_stats(brand_id)

        # Log scrape
        self.log_scrape(brand_id, brand_name, len(products_list), inserted, updated, errors)

        return inserted, updated, errors

    def update_brand_stats(self, brand_id):
        """Update brand document with latest stats"""
        product_count = self.products.count_documents({'brand_id': brand_id})

        self.brands.update_one(
            {'brand_id': brand_id},
            {
                '$set': {
                    'product_count': product_count,
                    'last_scraped': datetime.now(),
                    'display_name': brand_id  # Ensure display_name is set
                }
            },
            upsert=True
        )

    def log_price(self, product_id, brand_id, price, compare_price=None):
        """Log price history"""
        price_entry = {
            'product_id': product_id,
            'brand_id': brand_id,
            'price': price,
            'compare_at_price': compare_price,
            'date': datetime.now()
        }

        self.price_history.insert_one(price_entry)

    def log_scrape(self, brand_id, brand_name, total, inserted, updated, errors):
        """Log scraping activity"""
        log_entry = {
            'brand_id': brand_id,
            'brand_name': brand_name,
            'timestamp': datetime.now(),
            'total_products': total,
            'inserted': inserted,
            'updated': updated,
            'errors': errors,
            'status': 'success' if errors == 0 else 'partial'
        }

        self.scrape_logs.insert_one(log_entry)

    def get_stats(self):
        """Get overall database statistics"""
        brands = list(self.brands.find())

        stats = {
            'total_brands': len(brands),
            'total_products': self.products.count_documents({}),
            'total_price_records': self.price_history.count_documents({}),
            'brands_summary': []
        }

        for brand in brands:
            product_count = self.products.count_documents({'brand_id': brand['brand_id']})
            stats['brands_summary'].append({
                'brand_id': brand['brand_id'],
                'name': brand.get('display_name', brand['brand_id']),
                'product_count': product_count,
                'last_scraped': brand.get('last_scraped')
            })

        return stats

    def close(self):
        """Close database connection"""
        self.client.close()


# ============================================
# FUNCTION: Find Latest JSON File
# ============================================
def find_latest_file(brand_id, pattern):
    """Find the most recent JSON file for a brand"""
    search_pattern = os.path.join(DATA_DIR, pattern)
    files = glob.glob(search_pattern)

    if not files:
        return None

    # Get the most recent file
    latest_file = max(files, key=os.path.getctime)
    return latest_file


# ============================================
# FUNCTION: Import Brand Data
# ============================================
def import_brand_data(brand_id, json_file, db):
    """Import a brand's JSON data into MongoDB"""

    brand_names = {
        'nishat': 'Nishat Linen',
        'ethnic': 'Ethnic',
        'gulahmed': 'Gul Ahmed',
        'generation': 'Generation',
        'crossstitch': 'Cross Stitch',
        'mariab': 'Maria B',
        'limelight': 'Limelight'
    }

    brand_name = brand_names.get(brand_id, brand_id)

    print(f"\n{'=' * 60}")
    print(f"Importing: {brand_name}")
    print(f"File: {json_file}")
    print(f"{'=' * 60}")

    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            products = json.load(f)

        print(f"📂 Loaded {len(products)} products")

        inserted, updated, errors = db.insert_products_bulk(products, brand_id, brand_name)

        print(f"✅ Inserted: {inserted}, Updated: {updated}, Errors: {errors}")

        return True

    except Exception as e:
        print(f"❌ Error importing {brand_name}: {e}")
        return False


# ============================================
# MAIN EXECUTION
# ============================================
if __name__ == "__main__":
    print("""
    ╔═══════════════════════════════════════════════════════╗
    ║                                                       ║
    ║                 VASTR PROJECT                         ║
    ║        Auto-Import All Brands to MongoDB              ║
    ║                                                       ║
    ╚═══════════════════════════════════════════════════════╝
    """)

    if not os.path.exists(DATA_DIR):
        print(f"❌ Error: Data directory not found: {DATA_DIR}")
        print("Please run the scraper first to generate data files.")
        exit(1)

    print("\n🔌 Connecting to MongoDB...")
    db = VastrDatabase()

    successful = 0
    failed = 0

    for brand_id, file_pattern in BRAND_FILES.items():
        json_file = find_latest_file(brand_id, file_pattern)

        if json_file:
            success = import_brand_data(brand_id, json_file, db)
            if success:
                successful += 1
            else:
                failed += 1
        else:
            print(f"\n⚠️  No data file found for {brand_id}")
            print(f"   Looking for: {file_pattern}")
            failed += 1

    print("\n" + "=" * 60)
    print("IMPORT COMPLETE - DATABASE STATISTICS")
    print("=" * 60)

    stats = db.get_stats()

    print(f"\n📊 Total Brands: {stats['total_brands']}")
    print(f"📦 Total Products: {stats['total_products']}")
    print(f"💰 Price Records: {stats['total_price_records']}")

    print(f"\n🏪 Brand Breakdown:")
    for brand in stats['brands_summary']:
        last_scraped = brand['last_scraped'].strftime('%Y-%m-%d %H:%M') if brand['last_scraped'] else 'Never'
        print(f"   {brand['name']}: {brand['product_count']} products (Last: {last_scraped})")

    print(f"\n✅ Successfully imported: {successful} brands")
    if failed > 0:
        print(f"❌ Failed to import: {failed} brands")

    db.close()

    print("\n✅ All data imported successfully!")
    print("\nYour database is now ready for:")
    print("• Price comparison analysis")
    print("• Product search and filtering")
    print("• Trend analysis")
    print("• Building the frontend application")