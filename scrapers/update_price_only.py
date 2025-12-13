"""
Re-scrape Nishat Linen products and update ONLY prices in database
This preserves all your existing data (embeddings, etc.) and just fixes prices
"""

import requests
import time
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

# MongoDB connection
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
client = MongoClient(MONGODB_URI)
db = client["vastr"]
collection = db["products"]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

CLOTHING_COLLECTIONS = [
    'new-in-unstitched',
    'unstitched',
    'ready-to-wear-1',
    'ready-to-stitch',
    'luxury',
    'pret',
    'bottoms',
    'freedom-to-buy',
    'sale',
]


def scrape_collection(collection_handle):
    """Scrape all products from a specific collection"""
    all_products = []
    page = 1

    ACCESSORY_KEYWORDS = [
        'shoe', 'shoes', 'heels', 'khussa', 'kolhapuri', 'sneaker', 'slipper', 'sandal',
        'bag', 'clutch', 'handbag', 'wallet', 'purse',
        'jewelry', 'jewellery', 'earring', 'necklace', 'bracelet', 'ring',
        'perfume', 'fragrance', 'scent', 'candle',
        'accessory', 'accessories', 'dupatta-only', 'shawl-only'
    ]

    while True:
        url = f"https://nishatlinen.com/collections/{collection_handle}/products.json?page={page}&limit=250"
        print(f"   Page {page}...", end=" ")

        try:
            response = requests.get(url, headers=HEADERS)

            if response.status_code == 200:
                data = response.json()
                products = data.get('products', [])

                if not products:
                    print("Done!")
                    break

                # Filter out accessories
                clothing_products = []
                for product in products:
                    product_type = product.get('product_type', '').lower()
                    title = product.get('title', '').lower()
                    tags = ' '.join(product.get('tags', [])).lower()

                    is_accessory = any(keyword in product_type or keyword in title or keyword in tags
                                       for keyword in ACCESSORY_KEYWORDS)

                    if not is_accessory:
                        clothing_products.append(product)

                all_products.extend(clothing_products)
                print(f"Got {len(clothing_products)} items")

                page += 1
                time.sleep(2)
            else:
                print(f"Error: Status {response.status_code}")
                break

        except Exception as e:
            print(f"Error: {e}")
            break

    return all_products


def update_product_prices():
    """Re-scrape products and update only prices in database"""

    print("\n" + "=" * 70)
    print("UPDATING NISHAT LINEN PRICES FROM WEBSITE")
    print("=" * 70)
    print("\nThis will:")
    print("  ✓ Re-scrape current prices from nishatlinen.com")
    print("  ✓ Update ONLY prices in your database")
    print("  ✓ Keep all other data (images, embeddings, etc.)")
    print("\n" + "=" * 70)

    confirm = input("\nStart price update? (yes/no): ")
    if confirm.lower() != 'yes':
        print("Cancelled.")
        return

    print("\nStarting scrape...\n")

    all_products = []

    # Scrape from all collections
    for collection_handle in CLOTHING_COLLECTIONS:
        print(f"\nCollection: {collection_handle}")
        products = scrape_collection(collection_handle)
        all_products.extend(products)
        print(f"   Collection total: {len(products)} items")

    # Remove duplicates
    print("\nRemoving duplicates...")
    unique_products = {p['id']: p for p in all_products}.values()
    all_products = list(unique_products)

    print(f"Total unique products scraped: {len(all_products)}")

    if not all_products:
        print("No products found!")
        return

    # Update prices in database
    print("\nUpdating prices in database...")
    updated_count = 0
    not_found_count = 0
    skipped_count = 0

    for product in all_products:
        try:
            # Calculate prices from variants
            variants = product.get('variants', [])
            prices = [float(v.get('price', 0)) for v in variants if v.get('price')]

            if not prices:
                skipped_count += 1
                continue

            min_price = min(prices)
            max_price = max(prices)

            # Find product in database by Shopify product ID
            product_id = str(product.get('id'))

            # Try to find by product_id field
            result = collection.update_one(
                {"product_id": product_id},
                {
                    "$set": {
                        "price_min": min_price,
                        "price_max": max_price
                    }
                }
            )

            if result.matched_count > 0:
                updated_count += 1
                if updated_count % 50 == 0:
                    print(f"  Updated {updated_count} products...")
            else:
                not_found_count += 1

        except Exception as e:
            print(f"  Error updating {product.get('title', 'Unknown')}: {e}")
            continue

    print("\n" + "=" * 70)
    print("PRICE UPDATE COMPLETE")
    print("=" * 70)
    print(f"✓ Successfully updated: {updated_count} products")
    print(f"⚠️  Not found in DB: {not_found_count} products")
    print(f"⚠️  Skipped (no price): {skipped_count} products")

    # Verify the fix
    verify_prices()


def verify_prices():
    """Check if prices look correct now"""
    print("\n" + "=" * 70)
    print("VERIFYING PRICES")
    print("=" * 70)

    # Check for remaining low prices
    low_prices = collection.count_documents({
        "brand_name": "Nishat Linen",
        "price_min": {"$lt": 500, "$gt": 0}
    })

    if low_prices > 0:
        print(f"\n⚠️  Still {low_prices} Nishat products with prices < 500 PKR")
        print("These might need manual review.")
    else:
        print("\n✓ No suspiciously low prices found!")

    # Show sample prices
    samples = collection.find({
        "brand_name": "Nishat Linen",
        "price_min": {"$gt": 0}
    }).limit(5)

    print("\nSample Nishat Linen prices:")
    for product in samples:
        title = product.get('title', 'Unknown')[:60]
        price = product.get('price_min', 0)
        print(f"  {title}")
        print(f"    Price: PKR {price:.0f}")


def show_stats():
    """Show current database statistics"""
    print("\n" + "=" * 70)
    print("CURRENT DATABASE STATISTICS")
    print("=" * 70)

    # Total products
    total = collection.count_documents({})
    print(f"\nTotal products: {total}")

    # Nishat products
    nishat_total = collection.count_documents({"brand_name": "Nishat Linen"})
    print(f"Nishat Linen products: {nishat_total}")

    # Products with low prices
    low_prices = collection.count_documents({
        "brand_name": "Nishat Linen",
        "price_min": {"$lt": 500, "$gt": 0}
    })
    print(f"Nishat products with prices < 500 PKR: {low_prices}")

    if low_prices > 0:
        print("\n⚠️  These prices are likely incorrect and need updating!")
    else:
        print("\n✓ All prices look good!")

    # Price range
    pipeline = [
        {"$match": {"brand_name": "Nishat Linen", "price_min": {"$gt": 0}}},
        {"$group": {
            "_id": None,
            "min": {"$min": "$price_min"},
            "max": {"$max": "$price_min"},
            "avg": {"$avg": "$price_min"}
        }}
    ]

    stats = list(collection.aggregate(pipeline))
    if stats:
        stat = stats[0]
        print(f"\nNishat Linen price range:")
        print(f"  Lowest:  PKR {stat['min']:.0f}")
        print(f"  Highest: PKR {stat['max']:.0f}")
        print(f"  Average: PKR {stat['avg']:.0f}")


def main():
    """Main menu"""
    while True:
        print("\n" + "=" * 70)
        print("NISHAT LINEN PRICE UPDATE TOOL")
        print("=" * 70)
        print("1. Show current database statistics")
        print("2. Update prices from website (recommended)")
        print("3. Verify prices after update")
        print("4. Exit")
        print("=" * 70)

        choice = input("\nSelect option (1-4): ")

        if choice == "1":
            show_stats()
        elif choice == "2":
            update_product_prices()
        elif choice == "3":
            verify_prices()
        elif choice == "4":
            print("Goodbye!")
            break
        else:
            print("Invalid choice!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nCancelled by user.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
    finally:
        client.close()