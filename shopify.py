"""
Vastr - Platform Checker for Pakistani Fashion Stores
Identify which stores use Shopify (easy API access)
"""

import requests
from bs4 import BeautifulSoup
import time

# ============================================
# Pakistani Fashion Stores to Check
# ============================================
STORES_TO_CHECK = {
    # Already confirmed
    'Gul Ahmed': 'https://www.gulahmedshop.com',
    'Nishat Linen': 'https://nishatlinen.com',
    'Ethnic': 'https://www.ethnic.pk',
    'Khaadi': 'https://pk.khaadi.com',
    'Sapphire': 'https://pk.sapphireonline.pk',

    # Additional popular stores
    'Generation': 'https://generation.com.pk',
    'Alkaram': 'https://www.alkaramstudio.com',
    'Bonanza Satrangi': 'https://www.bonanzasatrangi.com',
    'Junaid Jamshed': 'https://www.jj.com.pk',
    'Limelight': 'https://www.limelight.pk',
    'Maria B': 'https://www.mariab.pk',
    'Sana Safinaz': 'https://www.sanasafinaz.com',
    'Zara Shahjahan': 'https://www.zarashahjahan.com',
    'Crossroads': 'https://www.crossroads.pk',
    'Outfitters': 'https://www.outfitters.com.pk',
    'Breakout': 'https://www.breakout.com.pk',
    'Ideas': 'https://ideas.com.pk',
    'Ego': 'https://www.ego.com.pk',
    'Zeen': 'https://www.zeenwoman.com',
    'Asim Jofa': 'https://www.asimjofa.com',
}


# ============================================
# FUNCTION: Check Platform
# ============================================
def check_platform(store_name, url):
    """
    Check what e-commerce platform a store uses
    """
    print(f"\n{'=' * 60}")
    print(f"Checking: {store_name}")
    print(f"URL: {url}")
    print(f"{'=' * 60}")

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code != 200:
            print(f"❌ Failed to access (Status: {response.status_code})")
            return None

        html = response.text.lower()
        soup = BeautifulSoup(response.content, 'html.parser')

        # Check for platform indicators
        platform = 'Unknown'
        api_available = False

        # Shopify detection
        if 'shopify' in html or 'cdn.shopify.com' in html:
            platform = 'Shopify'
            api_available = True
            print("✅ Platform: Shopify")

            # Try Shopify API
            api_url = f"{url.rstrip('/')}/products.json?limit=1"
            try:
                api_response = requests.get(api_url, timeout=5)
                if api_response.status_code == 200:
                    data = api_response.json()
                    if data.get('products'):
                        print(f"   ✅ Shopify API works! ({len(data['products'])} sample products)")
                    else:
                        print("   ⚠️  API accessible but no products")
                else:
                    print(f"   ⚠️  API returned status {api_response.status_code}")
            except:
                print("   ⚠️  API test failed")

        # Demandware/Salesforce Commerce Cloud
        elif 'demandware' in html or 'salesforce' in html:
            platform = 'Demandware/Salesforce'
            api_available = False
            print("❌ Platform: Demandware (No easy API)")

        # Magento
        elif 'magento' in html or 'mage' in html:
            platform = 'Magento'
            api_available = False
            print("⚠️  Platform: Magento (Complex API)")

        # WooCommerce
        elif 'woocommerce' in html or 'wp-content' in html:
            platform = 'WooCommerce'
            api_available = True
            print("⚠️  Platform: WooCommerce (API available with auth)")

        # Custom
        else:
            platform = 'Custom/Unknown'
            api_available = False
            print("⚠️  Platform: Custom or Unknown")

        return {
            'store': store_name,
            'url': url,
            'platform': platform,
            'api_available': api_available,
            'status': response.status_code
        }

    except requests.exceptions.Timeout:
        print(f"⏱️  Timeout - site too slow")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


# ============================================
# FUNCTION: Test Shopify API
# ============================================
def test_shopify_api(url):
    """
    Test if Shopify API is accessible
    """
    endpoints = [
        '/products.json?limit=5',
        '/collections.json',
    ]

    for endpoint in endpoints:
        test_url = f"{url.rstrip('/')}{endpoint}"
        try:
            response = requests.get(test_url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ {endpoint}: Works!")
                return True
        except:
            pass

    return False


# ============================================
# MAIN EXECUTION
# ============================================
if __name__ == "__main__":
    print("""
    ╔═══════════════════════════════════════════════════════╗
    ║                                                       ║
    ║        VASTR - Platform Checker                       ║
    ║     Finding Shopify Stores for Easy Scraping         ║
    ║                                                       ║
    ╚═══════════════════════════════════════════════════════╝
    """)

    results = []

    # Check all stores
    for store_name, url in STORES_TO_CHECK.items():
        result = check_platform(store_name, url)
        if result:
            results.append(result)
        time.sleep(2)  # Be respectful, wait between requests

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY REPORT")
    print("=" * 60)

    shopify_stores = [r for r in results if r['platform'] == 'Shopify']
    demandware_stores = [r for r in results if 'Demandware' in r['platform']]
    other_stores = [r for r in results if r not in shopify_stores + demandware_stores]

    print(f"\n✅ SHOPIFY STORES (Easy - Free API):")
    print(f"Total: {len(shopify_stores)}")
    for store in shopify_stores:
        print(f"   • {store['store']}")
        print(f"     {store['url']}")

    print(f"\n❌ DEMANDWARE STORES (Hard - Need Apify):")
    print(f"Total: {len(demandware_stores)}")
    for store in demandware_stores:
        print(f"   • {store['store']}")

    print(f"\n⚠️  OTHER PLATFORMS:")
    print(f"Total: {len(other_stores)}")
    for store in other_stores:
        print(f"   • {store['store']}: {store['platform']}")

    # Recommendation
    print("\n" + "=" * 60)
    print("RECOMMENDATION FOR VASTR PROJECT")
    print("=" * 60)

    if len(shopify_stores) >= 5:
        print(f"\n🎯 Great news! You have {len(shopify_stores)} Shopify stores.")
        print("Recommended brands to use (all Shopify):")
        for i, store in enumerate(shopify_stores[:5], 1):
            print(f"   {i}. {store['store']}")
        print("\n✅ Benefits:")
        print("   • Free JSON API access (no Apify credits needed)")
        print("   • Easy to scrape")
        print("   • Consistent data structure")
    else:
        print(f"\n⚠️  Only {len(shopify_stores)} Shopify stores found.")
        print("You'll need to use Apify for non-Shopify stores.")

    # Save results
    import json

    with open('data/platform_check_results.json', 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n💾 Full results saved to: data/platform_check_results.json")