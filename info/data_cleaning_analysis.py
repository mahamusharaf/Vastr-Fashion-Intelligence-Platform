from pymongo import MongoClient
import pandas as pd
import json
from datetime import datetime
import os

# ============================================
# CONFIGURATION
# ============================================
MONGO_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "vastr_fashion_db"
OUTPUT_DIR = "../reports"

BRAND_FILES = {
    'nishat': 'Nishat Linen',
    'ethnic': 'Ethnic',
    'gulahmed': 'Gul Ahmed',
    'generation': 'Generation',
    'crossstitch': 'Cross Stitch',
    'mariab': 'Maria B',
    'limelight': 'Limelight'
}

# Category mapping function using product_type, title, and tags
def map_category(ptype, title, tags):
    ptype = ptype.lower().strip() if isinstance(ptype, str) else 'unknown'
    title = title.lower() if isinstance(title, str) else ''
    tags = [t.lower() for t in tags] if isinstance(tags, list) else []

    # Direct mappings for known product_type values
    CATEGORY_MAPPING = {
        'pack suit': 'Unstitched',
        'suit': 'Unstitched',
        'lawn suit': 'Unstitched',
        'embroidered suit': 'Unstitched',
        'unstitched': 'Unstitched',
        'unstitched printed': 'Unstitched',
        'unstitched embroidered': 'Unstitched',
        'unstitched embroidery': 'Unstitched',
        'unstitched lawn': 'Unstitched',
        'unstitched mbroidered': 'Unstitched',
        'unstitched printed-2': 'Unstitched',
        'unstitched trouser': 'Trousers',
        'unstitched trouser-1': 'Trousers',
        'unstitched (medium emb)-1': 'Unstitched',
        'unstitched emb-old': 'Unstitched',
        'unstitched-rozana': 'Unstitched',
        'pret': 'Ready-to-Wear',
        'ready to wear': 'Ready-to-Wear',
        'rtw': 'Ready-to-Wear',
        'ready to wear-old': 'Ready-to-Wear',
        'exclusive pret': 'Ready-to-Wear',
        'luxury pret': 'Ready-to-Wear',
        'basic pret': 'Ready-to-Wear',
        'wedding pret': 'Ready-to-Wear',
        'kurta': 'Kurta',
        'kurtas': 'Kurta',
        'basic suits': 'Unstitched',
        'exclusive suits': 'Unstitched',
        'luxury suits': 'Unstitched',
        'men suit': 'Menswear',
        'women': 'Unstitched',  # Assume women with lawn/suit context
        'women fabric': 'Unstitched',
        'silk pants': 'Trousers',
        'exclusive pants': 'Trousers',
        'basic pants': 'Trousers',
        'trousers': 'Trousers',
        'trousers-old': 'Trousers',
        'bottoms': 'Trousers',
        'bottom': 'Trousers',
        'western': 'Western',
        'western-1': 'Western',
        'western-old': 'Western',
        'co-ords': 'Western',
        'eastern top': 'Kurta',
        'eastern top-2': 'Kurta',
        'tops': 'Western',
        'luxury formals': 'Ready-to-Wear',
        'rozana': 'Ready-to-Wear',
        'casual': 'Ready-to-Wear',
        'studio': 'Ready-to-Wear',
        'fusion': 'Ready-to-Wear',
        'winter': 'Ready-to-Wear',
        'winters': 'Ready-to-Wear',
        'shawls': 'Others',
        'loungewear': 'Others',
        'knit': 'Ready-to-Wear',
        'meter': 'Unstitched'
    }

    # Direct mapping if product_type is known
    if ptype in CATEGORY_MAPPING:
        return CATEGORY_MAPPING[ptype]

    # Dynamic mapping based on title and tags
    if any(keyword in title or keyword in tags for keyword in ['unstitched', 'lawn', 'suit', 'piece', 'fabric']):
        return 'Unstitched'
    if any(keyword in title or keyword in tags for keyword in ['pret', 'rtw', 'stitched', 'ready to wear', 'luxury pret', 'casual']):
        return 'Ready-to-Wear'
    if any(keyword in title or keyword in tags for keyword in ['kurta', 'kurtas']):
        return 'Kurta'
    if any(keyword in title or keyword in tags for keyword in ['pant', 'trouser', 'bottom', 'pants']):
        return 'Trousers'
    if any(keyword in title or keyword in tags for keyword in ['western', 'co-ord', 'top', 'tops']):
        return 'Western'
    if any(keyword in title or keyword in tags for keyword in ['men', 'menswear']):
        return 'Menswear'
    return 'Others'

# ============================================
# DATABASE CONNECTION AND ANALYSIS
# ============================================
class DataAnalyzer:
    """Analyze Vastr fashion data"""

    def __init__(self):
        self.client = MongoClient(MONGO_URI)
        self.db = self.client[DATABASE_NAME]
        self.products = self.db['products']
        self.brands = self.db['brands']
        print("✅ Connected to database")

    def get_all_products_df(self):
        """Load all products into pandas DataFrame"""
        products = list(self.products.find())
        if not products:
            print("❌ No products found in database!")
            return None
        df = pd.DataFrame(products)
        print(f"📊 Loaded {len(df)} products")

        # Map brand_id to brand_name
        if 'brand_id' in df.columns:
            df['brand_name'] = df['brand_id'].map(BRAND_FILES).fillna(df['brand_id'])

        # Standardize product_type using title and tags
        if 'product_type' in df.columns:
            df['product_type'] = df.apply(
                lambda row: map_category(
                    row['product_type'],
                    row.get('title', ''),
                    row.get('tags', [])
                ), axis=1
            )
        return df

    def data_quality_report(self, df):
        """Generate data quality report"""
        print("\n" + "=" * 60)
        print("DATA QUALITY REPORT")
        print("=" * 60)

        print("\n📋 Missing Data Analysis:")
        missing = df.isnull().sum()
        total = len(df)
        key_fields = ['title', 'price_min', 'brand_id', 'product_type', 'available', 'images']
        for field in key_fields:
            if field in df.columns:
                missing_count = df[field].isnull().sum()
                missing_pct = (missing_count / total) * 100
                print(f"   {field}: {missing_count} missing ({missing_pct:.1f}%)")

        print("\n🔍 Data Consistency:")
        if 'price_min' in df.columns:
            print(f"   Products with price_min: {df['price_min'].notna().sum()} ({(df['price_min'].notna().sum() / total) * 100:.1f}%)")
        print(f"   Products with images: {df['images'].apply(lambda x: len(x) > 0 if isinstance(x, list) else False).sum()}")
        print(f"   Available products: {df['available'].sum() if 'available' in df else 'N/A'}")
        if 'product_id' in df.columns:
            duplicates = df.duplicated(subset=['product_id']).sum()
            print(f"   Duplicate product IDs: {duplicates}")

        return {
            'total_products': total,
            'missing_prices': df['price_min'].isnull().sum() if 'price_min' in df.columns else 0,
            'missing_images': df['images'].apply(lambda x: len(x) == 0 if isinstance(x, list) else True).sum()
        }

    def price_analysis(self, df):
        """Analyze pricing across brands"""
        print("\n" + "=" * 60)
        print("PRICE ANALYSIS")
        print("=" * 60)

        price_col = 'price_min'
        df_with_price = df[df[price_col].notna() & (df[price_col] > 0)].copy()

        print(f"\n💰 Overall Price Statistics:")
        print(f"   Total products with prices: {len(df_with_price)}")
        print(f"   Average price: PKR {df_with_price[price_col].mean():,.2f}")
        print(f"   Median price: PKR {df_with_price[price_col].median():,.2f}")
        print(f"   Min price: PKR {df_with_price[price_col].min():,.2f}")
        print(f"   Max price: PKR {df_with_price[price_col].max():,.2f}")

        print(f"\n🏪 Average Price by Brand:")
        brand_prices = df_with_price.groupby('brand_name')[price_col].agg(['mean', 'median', 'min', 'max', 'count'])
        brand_prices = brand_prices.sort_values('mean', ascending=False)

        for brand, row in brand_prices.iterrows():
            print(f"\n   {brand}:")
            print(f"      Products: {int(row['count'])}")
            print(f"      Avg: PKR {row['mean']:,.2f}")
            print(f"      Median: PKR {row['median']:,.2f}")
            print(f"      Range: PKR {row['min']:,.2f} - PKR {row['max']:,.2f}")

        print(f"\n📊 Price Distribution:")
        bins = [0, 2000, 5000, 10000, 20000, float('inf')]
        labels = ['Budget (<2K)', 'Affordable (2K-5K)', 'Mid-range (5K-10K)', 'Premium (10K-20K)', 'Luxury (>20K)']
        df_with_price['price_range'] = pd.cut(df_with_price[price_col], bins=bins, labels=labels)
        price_dist = df_with_price['price_range'].value_counts().sort_index()
        for range_name, count in price_dist.items():
            pct = (count / len(df_with_price)) * 100
            print(f"   {range_name}: {count} products ({pct:.1f}%)")

        return brand_prices

    def category_analysis(self, df):
        """Analyze product categories"""
        print("\n" + "=" * 60)
        print("CATEGORY ANALYSIS")
        print("=" * 60)

        if 'product_type' in df.columns:
            print(f"\n📦 Top Product Categories (Overall):")
            categories = df['product_type'].value_counts().head(15)
            for cat, count in categories.items():
                pct = (count / len(df)) * 100
                print(f"   {cat}: {count} products ({pct:.1f}%)")

            print(f"\n🏪 Categories per Brand:")
            for brand in df['brand_name'].unique():
                brand_df = df[df['brand_name'] == brand]
                unique_cats = brand_df['product_type'].nunique()
                print(f"   {brand}: {unique_cats} unique categories")
                if unique_cats > 0:
                    brand_cats = brand_df['product_type'].value_counts()
                    for cat, count in brand_cats.items():
                        print(f"      {cat}: {count} products")

            unique_types = sorted(df['product_type'].unique())
            print(f"\n🔍 All Unique Product Types ({len(unique_types)}):")
            print(f"   {unique_types}")
        else:
            print("\n⚠️ No product_type field found in data")

    def brand_comparison(self, df):
        """Compare brands"""
        print("\n" + "=" * 60)
        print("BRAND COMPARISON")
        print("=" * 60)

        price_col = 'price_min'
        brand_stats = []
        for brand in df['brand_name'].unique():
            brand_df = df[df['brand_name'] == brand]
            stats = {
                'brand': brand,
                'total_products': len(brand_df),
                'avg_price': brand_df[price_col].mean() if price_col in brand_df else 0,
                'available_products': brand_df['available'].sum() if 'available' in brand_df else 0,
                'products_with_images': brand_df['images'].apply(
                    lambda x: len(x) > 0 if isinstance(x, list) else False).sum(),
                'avg_images_per_product': brand_df['images'].apply(
                    lambda x: len(x) if isinstance(x, list) else 0).mean()
            }
            brand_stats.append(stats)

        brand_stats.sort(key=lambda x: x['total_products'], reverse=True)
        print(f"\n🏆 Brand Rankings:")
        for i, stats in enumerate(brand_stats, 1):
            print(f"\n   {i}. {stats['brand']}")
            print(f"      Products: {stats['total_products']}")
            print(f"      Avg Price: PKR {stats['avg_price']:,.2f}")
            print(f"      Available: {stats['available_products']}")
            print(f"      With Images: {stats['products_with_images']}")
            print(f"      Avg Images/Product: {stats['avg_images_per_product']:.1f}")

        return brand_stats

    def generate_insights(self, df):
        """Generate key insights"""
        print("\n" + "=" * 60)
        print("KEY INSIGHTS & RECOMMENDATIONS")
        print("=" * 60)

        insights = []
        price_col = 'price_min'
        brand_avg_prices = df.groupby('brand_name')[price_col].mean().sort_values(ascending=False)
        most_expensive = brand_avg_prices.index[0]
        insights.append(
            f"🔹 {most_expensive} is the most premium brand (Avg: PKR {brand_avg_prices[most_expensive]:,.2f})")
        most_affordable = brand_avg_prices.index[-1]
        insights.append(
            f"🔹 {most_affordable} offers most affordable options (Avg: PKR {brand_avg_prices[most_affordable]:,.2f})")
        brand_counts = df['brand_name'].value_counts()
        largest_inventory = brand_counts.index[0]
        insights.append(
            f"🔹 {largest_inventory} has the largest collection ({brand_counts[largest_inventory]} products)")
        mid_range_count = df[(df[price_col] >= 5000) & (df[price_col] <= 10000)].shape[0]
        mid_range_pct = (mid_range_count / len(df)) * 100
        insights.append(f"🔹 {mid_range_pct:.1f}% of products are in mid-range (5K-10K PKR)")
        if 'product_type' in df.columns:
            others_count = df['product_type'].value_counts().get('Others', 0)
            others_pct = (others_count / len(df)) * 100
            if others_pct > 10:
                insights.append(f"⚠️ 'Others' category is large ({others_pct:.1f}% of products) - refine scraping scripts for better categorization")

        print("\n")
        for insight in insights:
            print(f"   {insight}")

        return insights

    def export_analysis(self, df, brand_prices, brand_stats, insights):
        """Export analysis results"""
        print("\n" + "=" * 60)
        print("EXPORTING ANALYSIS")
        print("=" * 60)

        os.makedirs(OUTPUT_DIR, exist_ok=True)

        def convert_types(obj):
            if isinstance(obj, dict):
                return {k: convert_types(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_types(item) for item in obj]
            elif hasattr(obj, 'item'):
                return obj.item()
            elif pd.isna(obj):
                return None
            return obj

        report = {
            'generated_at': datetime.now().isoformat(),
            'total_products': int(len(df)),
            'total_brands': int(df['brand_name'].nunique()),
            'price_statistics': {
                'average': convert_types(df['price_min'].mean()) if 'price_min' in df else 0,
                'median': convert_types(df['price_min'].median()) if 'price_min' in df else 0,
                'min': convert_types(df['price_min'].min()) if 'price_min' in df else 0,
                'max': convert_types(df['price_min'].max()) if 'price_min' in df else 0
            },
            'category_statistics': convert_types({
                brand: dict(df[df['brand_name'] == brand]['product_type'].value_counts())
                for brand in df['brand_name'].unique()
            }) if 'product_type' in df.columns else {},
            'brand_prices': convert_types(brand_prices.to_dict()) if brand_prices is not None else {},
            'brand_stats': convert_types(brand_stats),
            'insights': insights
        }

        with open(f'{OUTPUT_DIR}/analysis_summary.json', 'w') as f:
            json.dump(report, f, indent=2)
        print(f"✅ Saved: {OUTPUT_DIR}/analysis_summary.json")

        export_cols = ['brand_name', 'title', 'price_min', 'product_type', 'available', 'url']
        export_cols = [col for col in export_cols if col in df.columns]
        df_export = df[export_cols].copy()
        df_export.to_csv(f'{OUTPUT_DIR}/products_analysis.csv', index=False)
        print(f"✅ Saved: {OUTPUT_DIR}/products_analysis.csv")

        if brand_prices is not None:
            brand_prices.to_csv(f'{OUTPUT_DIR}/brand_price_comparison.csv')
            print(f"✅ Saved: {OUTPUT_DIR}/brand_price_comparison.csv")

    def close(self):
        """Close database connection"""
        self.client.close()

if __name__ == "__main__":

    analyzer = DataAnalyzer()
    print("\n📂 Loading data from MongoDB...")
    df = analyzer.get_all_products_df()

    if df is None:
        print("❌ Cannot proceed without data")
        exit(1)

    quality_report = analyzer.data_quality_report(df)
    brand_prices = analyzer.price_analysis(df)
    analyzer.category_analysis(df)
    brand_stats = analyzer.brand_comparison(df)
    insights = analyzer.generate_insights(df)
    analyzer.export_analysis(df, brand_prices, brand_stats, insights)
    analyzer.close()

    print("\n" + "=" * 60)
    print("✅ PHASE 2 ANALYSIS COMPLETE!")
    print("=" * 60)
    print(f"\n📊 Reports generated in '{OUTPUT_DIR}/' folder:")
    print("   • analysis_summary.json - Complete analysis")
    print("   • products_analysis.csv - Product details")
    print("   • brand_price_comparison.csv - Brand pricing")