import requests
import json
import time
from datetime import datetime

# Configuration
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}


# Multiple collections to get comprehensive clothing data
CLOTHING_COLLECTIONS = [
    'women',  # Main women's collection
    'unstitched-fabric',  # Unstitched fabrics
    'women-ideas-pret-signature',  # Ready-to-wear signature
    'women-ideas-pret-essentials',  # Pret essentials
    'women-ideas-pret-everyday-edit',  # Everyday edit
    'women-ideas-pret-9-to-5',  # Workwear
    'salt-western-wear-women',  # Western wear
    'women-unstitched-to-stitched',  # Unstitched to stitched
]


def scrape_collection(collection_handle, max_products=None):
    """Scrape all products from a specific collection"""
    all_products = []
    page = 1

    # Accessory keywords to filter out
    ACCESSORY_KEYWORDS = [
        'shoe', 'shoes', 'heels', 'khussa', 'kolhapuri', 'sneaker', 'slipper', 'sandal',
        'bag', 'clutch', 'handbag', 'wallet', 'purse',
        'jewelry', 'jewellery', 'earring', 'necklace', 'bracelet', 'ring',
        'perfume', 'fragrance', 'scent', 'candle',
        'accessory', 'accessories'
    ]

    while True:
        url = f"https://www.gulahmedshop.com/collections/{collection_handle}/products.json?page={page}&limit=250"
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

                    # Check if it's an accessory
                    is_accessory = any(keyword in product_type or keyword in title or keyword in tags
                                       for keyword in ACCESSORY_KEYWORDS)

                    if not is_accessory:
                        clothing_products.append(product)

                all_products.extend(clothing_products)
                print(
                    f"Got {len(clothing_products)} clothing items (filtered {len(products) - len(clothing_products)} accessories)")

                if max_products and len(all_products) >= max_products:
                    all_products = all_products[:max_products]
                    break

                page += 1
                time.sleep(2)  # Respectful delay
            else:
                print(f"Error: Status {response.status_code}")
                break

        except Exception as e:
            print(f"Error: {e}")
            break

    return all_products


def process_products(products):
    """Extract and structure key product information"""
    processed = []

    for product in products:
        try:
            # Get all variants
            variants = product.get('variants', [])

            # Get price range
            prices = [float(v.get('price', 0)) for v in variants if v.get('price')]
            min_price = min(prices) if prices else 0
            max_price = max(prices) if prices else 0

            # Get all images
            images = product.get('images', [])
            image_urls = [img.get('src') for img in images]

            # Get availability
            available = any(v.get('available', False) for v in variants)

            processed_product = {
                'id': product.get('id'),
                'title': product.get('title'),
                'handle': product.get('handle'),
                'product_type': product.get('product_type'),
                'vendor': product.get('vendor'),
                'tags': product.get('tags', []),
                'published_at': product.get('published_at'),
                'created_at': product.get('created_at'),
                'url': f"https://www.gulahmedshop.com/products/{product.get('handle')}",
                'price_min': min_price,
                'price_max': max_price,
                'available': available,
                'variant_count': len(variants),
                'image_count': len(images),
                'images': image_urls,
                'description': product.get('body_html', '')[:500],  # First 500 chars
                'variants': [{
                    'id': v.get('id'),
                    'title': v.get('title'),
                    'price': v.get('price'),
                    'sku': v.get('sku'),
                    'available': v.get('available'),
                    'inventory_quantity': v.get('inventory_quantity')
                } for v in variants]
            }

            processed.append(processed_product)

        except Exception as e:
            print(f"Error processing product {product.get('id')}: {e}")
            continue

    return processed


def analyze_data(products):
    """Analyze the scraped data"""
    if not products:
        return {}

    # Price analysis
    all_prices = [p['price_min'] for p in products if p['price_min'] > 0]

    # Product type breakdown
    product_types = {}
    for p in products:
        ptype = p.get('product_type', 'Unknown')
        product_types[ptype] = product_types.get(ptype, 0) + 1

    # Availability
    available_count = sum(1 for p in products if p['available'])

    analysis = {
        'total_products': len(products),
        'available_products': available_count,
        'unavailable_products': len(products) - available_count,
        'price_min': min(all_prices) if all_prices else 0,
        'price_max': max(all_prices) if all_prices else 0,
        'price_avg': sum(all_prices) / len(all_prices) if all_prices else 0,
        'product_types': product_types,
        'total_variants': sum(p['variant_count'] for p in products),
        'total_images': sum(p['image_count'] for p in products)
    }

    return analysis


def save_data(processed_data, raw_products):
    """Save data in multiple formats"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Save processed JSON
    json_file = f"data/gulahmed_clothing_{timestamp}.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(processed_data, f, indent=2, ensure_ascii=False)
    print(f"\nJSON saved: {json_file}")


    # Save analysis summary
    analysis = analyze_data(processed_data)
    summary_file = f"data/gulahmed_clothing_{timestamp}_summary.txt"
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("=" * 60 + "\n")
        f.write("GUL AHMED CLOTHING COLLECTION - SCRAPING SUMMARY\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Scrape Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        f.write("OVERVIEW:\n")
        f.write(f"Total Clothing Items: {analysis['total_products']}\n")
        f.write(f"Available: {analysis['available_products']}\n")
        f.write(f"Out of Stock: {analysis['unavailable_products']}\n")
        f.write(f"Total Variants: {analysis['total_variants']}\n")
        f.write(f"Total Images: {analysis['total_images']}\n\n")

        f.write("PRICE RANGE:\n")
        f.write(f"Minimum: PKR {analysis['price_min']:.2f}\n")
        f.write(f"Maximum: PKR {analysis['price_max']:.2f}\n")
        f.write(f"Average: PKR {analysis['price_avg']:.2f}\n\n")

        f.write("PRODUCT TYPES:\n")
        for ptype, count in sorted(analysis['product_types'].items(), key=lambda x: x[1], reverse=True):
            f.write(f"  {ptype}: {count}\n")

    print(f"Summary saved: {summary_file}")

    # Display summary
    print("\n" + "=" * 60)
    print("SCRAPING COMPLETE - SUMMARY")
    print("=" * 60)
    print(f"Total Clothing Items: {analysis['total_products']}")
    print(f"Available: {analysis['available_products']}")
    print(f"Price Range: PKR {analysis['price_min']:.0f} - PKR {analysis['price_max']:.0f}")
    print(f"\nTop Product Types:")
    for ptype, count in list(sorted(analysis['product_types'].items(), key=lambda x: x[1], reverse=True))[:5]:
        print(f"  {ptype}: {count}")


def main():
    print("\nStarting Gul Ahmed clothing scrape (accessories excluded)...\n")
    print("=" * 60)
    print(" Scraping from Multiple Clothing Collections")
    print("=" * 60)

    all_clothing = []

    # Scrape from multiple clothing collections
    for collection in CLOTHING_COLLECTIONS:
        print(f"\nCollection: {collection}")
        products = scrape_collection(collection)
        all_clothing.extend(products)
        print(f"   Collection total: {len(products)} items")

    # Remove duplicates (same product might appear in multiple collections)
    print("\nRemoving duplicates...")
    unique_products = {p['id']: p for p in all_clothing}.values()
    all_clothing = list(unique_products)

    print(f"\nTotal unique clothing items: {len(all_clothing)}")

    if not all_clothing:
        print("No clothing products found!")
        return

    # Process and save data
    print("\nProcessing product data...")
    processed_data = process_products(all_clothing)

    print("Saving data...")
    save_data(processed_data, all_clothing)

    print("\nDone!")


if __name__ == "__main__":
    main()