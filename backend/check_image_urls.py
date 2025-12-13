"""
check_image_urls.py
Run this to verify that image URLs in your database are valid and accessible
"""

import requests
from database import get_products_collection


def get_first_image_url(product):
    """Safely extract the first valid image URL from a product"""
    # Method 1: image_url field (some products use this)
    url = product.get("image_url")
    if url and isinstance(url, str) and url.strip().startswith(("http://", "https://")):
        return url.strip()

    # Method 2: images[] array (Shopify format)
    images = product.get("images") or []
    for img in images:
        src = img.get("src") if isinstance(img, dict) else None
        if src and isinstance(src, str) and src.strip().startswith(("http://", "https://")):
            return src.strip()

    return None


def check_url_accessible(url, timeout=15):
    """Check if URL returns 200 + actual image"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    try:
        r = requests.head(url, headers=headers, timeout=timeout, allow_redirects=True)
        if r.status_code == 200:
            ct = r.headers.get("content-type", "").lower()
            if "image" in ct or "octet-stream" in ct:
                return True, f"200 OK ({ct.split('/')[-1]})"
        elif r.status_code in (403, 404):
            return False, f"{r.status_code} {requests.status_codes._codes[r.status_code][0].upper()}"
        else:
            return False, f"{r.status_code}"
    except Exception as e:
        return False, f"Error: {str(e)[:40]}"


if __name__ == "__main__":
    print("\n" + "="*60)
    print("CHECKING IMAGE URLS IN DATABASE")
    print("="*60 + "\n")

    collection = get_products_collection()
    total = collection.count_documents({})
    print(f"Total products in DB: {total}\n")

    sample = list(collection.find().limit(25))

    print("Sample of 25 products:\n")
    ok_count = 0
    fail_count = 0

    for i, product in enumerate(sample, 1):
        title = product.get("title", "No title")[:60]
        url = get_first_image_url(product)

        print(f"[{i:2}] {title}")
        if not url:
            print(f"    image_url: None")
            print(f"    Status: FAILED - No valid image URL found")
            fail_count += 1
        else:
            accessible, msg = check_url_accessible(url)
            status = "OK" if accessible else "FAILED"
            color = "SUCCESS" if accessible else "FAILED"
            print(f"    URL: {url[:80]}{'...' if len(url)>80 else ''}")
            print(f"    Status: {status} - {msg}")
            if accessible:
                ok_count += 1
            else:
                fail_count += 1
        print()

    print("="*60)
    print(f"SUMMARY: {ok_count} OK, {fail_count} FAILED")
    if ok_count > 20:
        print("Image URLs look GOOD! Ready for embedding generation")
    else:
        print("Many URLs broken → fix product import or Shopify sync first")
    print("="*60)