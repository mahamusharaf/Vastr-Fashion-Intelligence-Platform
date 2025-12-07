"""
Vastr Fashion Intelligence Platform
Hybrid Search Engine: BM25 (Keyword) + Cosine Similarity (Semantic)

Save this file as: backend/hybrid_search.py
"""

from pymongo import MongoClient
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from rank_bm25 import BM25Okapi
import re
from typing import List, Dict, Tuple

# ============================================
# CONFIGURATION
# ============================================
MONGO_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "vastr_fashion_db"


# ============================================
# HYBRID SEARCH ENGINE
# ============================================
class VastrHybridSearch:
    """
    Hybrid Search combining BM25 and Cosine Similarity
    """

    def __init__(self):
        """Initialize search engine with MongoDB connection"""
        self.client = MongoClient(MONGO_URI)
        self.db = self.client[DATABASE_NAME]
        self.products = self.db['products']

        # Load all products
        self.products_list = list(self.products.find())
        print(f" Loaded {len(self.products_list)} products for search indexing")

        # Initialize search indices
        self.bm25_index = None
        self.tfidf_vectorizer = None
        self.tfidf_matrix = None
        self.product_texts = []

        # Build indices
        self._build_search_indices()

    def _preprocess_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""

        # Convert to lowercase
        text = text.lower()

        # Remove special characters but keep spaces and apostrophes
        text = re.sub(r'[^a-z0-9\s\']', ' ', text)

        # Remove extra whitespace
        text = ' '.join(text.split())

        return text

    def _expand_query(self, query: str) -> str:
        """
        Expand query with synonyms and related terms
        Helps with subjective/trendy fashion terms
        """
        query_lower = query.lower()

        # Fashion style synonyms
        style_expansions = {
            'aesthetic': ['trendy', 'stylish', 'fashionable', 'modern', 'chic'],
            'cute': ['pretty', 'beautiful', 'lovely', 'adorable', 'elegant'],
            'korean': ['kpop', 'asian', 'trendy', 'oversized', 'modern'],
            'casual': ['everyday', 'comfortable', 'relaxed', 'informal'],
            'formal': ['professional', 'office', 'business', 'elegant', 'sophisticated'],
            'vintage': ['retro', 'classic', 'traditional', 'old'],
            'boho': ['bohemian', 'hippie', 'flowy', 'ethnic'],
            'minimal': ['minimalist', 'simple', 'basic', 'plain', 'clean'],
            'luxury': ['premium', 'designer', 'high-end', 'expensive', 'exclusive']
        }

        # Occasion synonyms
        occasion_expansions = {
            'interview': ['formal', 'professional', 'office', 'business', 'corporate'],
            'wedding': ['bridal', 'party', 'formal', 'festive', 'celebration'],
            'party': ['evening', 'festive', 'celebration', 'occasion', 'special'],
            'casual': ['everyday', 'daily', 'comfort', 'relaxed'],
            'beach': ['summer', 'vacation', 'resort', 'light', 'breezy'],
            'eid': ['festive', 'celebration', 'traditional', 'special']
        }

        # Color variations
        color_expansions = {
            'black': ['dark', 'charcoal', 'noir'],
            'white': ['cream', 'ivory', 'off-white', 'pearl'],
            'red': ['maroon', 'crimson', 'scarlet', 'ruby'],
            'blue': ['navy', 'indigo', 'azure', 'cobalt'],
            'green': ['olive', 'emerald', 'mint', 'sage'],
            'pink': ['rose', 'blush', 'coral', 'salmon']
        }

        # Pattern/print synonyms
        pattern_expansions = {
            'floral': ['flower', 'botanical', 'garden', 'bloom', 'printed'],
            'striped': ['stripe', 'lines', 'linear'],
            'polka': ['dots', 'dotted', 'spotted'],
            'embroidered': ['embroidery', 'threadwork', 'hand-work', 'detailed']
        }

        # Expand query
        expanded_terms = [query]

        for word, synonyms in {**style_expansions, **occasion_expansions, **color_expansions,
                               **pattern_expansions}.items():
            if word in query_lower:
                expanded_terms.extend(synonyms[:3])  # Add top 3 synonyms

        return ' '.join(expanded_terms)

    def _create_searchable_text(self, product: Dict) -> str:
        """
        Create searchable text from product data
        Combines title, category, tags, description
        """
        parts = []

        # Title (most important - repeat 3x for higher weight)
        if product.get('title'):
            parts.extend([product['title']] * 3)

        # Product type (important - repeat 2x)
        if product.get('product_type'):
            parts.extend([product['product_type']] * 2)

        # Brand name
        if product.get('brand_name'):
            parts.append(product['brand_name'])

        # Tags
        if product.get('tags'):
            if isinstance(product['tags'], list):
                parts.extend(product['tags'])
            elif isinstance(product['tags'], str):
                parts.extend(product['tags'].split(','))

        # Description (lower weight - just once)
        if product.get('description'):
            # Take first 200 chars of description
            desc = product['description'][:200]
            parts.append(desc)

        # Vendor
        if product.get('vendor'):
            parts.append(product['vendor'])

        # Combine all parts
        searchable_text = ' '.join(str(p) for p in parts if p)

        return self._preprocess_text(searchable_text)

    def _build_search_indices(self):
        """Build BM25 and TF-IDF indices"""
        print("\n Building search indices...")

        # Create searchable text for each product
        self.product_texts = [
            self._create_searchable_text(product)
            for product in self.products_list
        ]

        # Build BM25 Index
        print("    Building BM25 index...")
        tokenized_corpus = [text.split() for text in self.product_texts]
        self.bm25_index = BM25Okapi(tokenized_corpus)
        print("    BM25 index built")

        # Build TF-IDF Index for Cosine Similarity
        print("    Building TF-IDF index...")
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=5000,
            ngram_range=(1, 2),  # Use unigrams and bigrams
            stop_words='english'
        )
        self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(self.product_texts)
        print("   TF-IDF index built")

        print(" Search indices ready!")

    def _bm25_search(self, query: str, top_k: int = 50) -> List[Tuple[int, float]]:
        """
        Perform BM25 keyword search
        Returns: List of (product_index, score) tuples
        """
        query_tokens = self._preprocess_text(query).split()
        bm25_scores = self.bm25_index.get_scores(query_tokens)

        # Get top K results
        top_indices = np.argsort(bm25_scores)[::-1][:top_k]
        results = [(idx, bm25_scores[idx]) for idx in top_indices if bm25_scores[idx] > 0]

        return results

    def _cosine_search(self, query: str, top_k: int = 50) -> List[Tuple[int, float]]:
        """
        Perform Cosine Similarity semantic search
        Returns: List of (product_index, score) tuples
        """
        # Transform query using TF-IDF
        query_vec = self.tfidf_vectorizer.transform([self._preprocess_text(query)])

        # Calculate cosine similarity
        cosine_scores = cosine_similarity(query_vec, self.tfidf_matrix).flatten()

        # Get top K results
        top_indices = np.argsort(cosine_scores)[::-1][:top_k]
        results = [(idx, cosine_scores[idx]) for idx in top_indices if cosine_scores[idx] > 0]

        return results

    def hybrid_search(
            self,
            query: str,
            top_k: int = 20,
            bm25_weight: float = 0.5,
            cosine_weight: float = 0.5,
            filters: Dict = None
    ) -> List[Dict]:
        """
        Perform hybrid search combining BM25 and Cosine Similarity

        Args:
            query: Search query
            top_k: Number of results to return
            bm25_weight: Weight for BM25 scores (0-1)
            cosine_weight: Weight for cosine scores (0-1)
            filters: Optional filters (brand_id, min_price, max_price, etc.)

        Returns:
            List of products with hybrid scores
        """
        print(f"\n Searching for: '{query}'")

        # Perform both searches
        bm25_results = self._bm25_search(query, top_k=100)
        cosine_results = self._cosine_search(query, top_k=100)

        # Normalize scores to 0-1 range
        def normalize_scores(results):
            if not results:
                return {}
            max_score = max(score for _, score in results)
            if max_score == 0:
                return {}
            return {idx: score / max_score for idx, score in results}

        bm25_normalized = normalize_scores(bm25_results)
        cosine_normalized = normalize_scores(cosine_results)

        # Combine scores
        hybrid_scores = {}
        all_indices = set(bm25_normalized.keys()) | set(cosine_normalized.keys())

        for idx in all_indices:
            bm25_score = bm25_normalized.get(idx, 0)
            cosine_score = cosine_normalized.get(idx, 0)

            # Weighted combination
            hybrid_score = (bm25_weight * bm25_score) + (cosine_weight * cosine_score)
            hybrid_scores[idx] = hybrid_score

        # Sort by hybrid score
        sorted_results = sorted(hybrid_scores.items(), key=lambda x: x[1], reverse=True)

        # Get top K products
        results = []
        for idx, score in sorted_results[:top_k]:
            product = self.products_list[idx].copy()

            # Apply filters if provided
            if filters:
                if not self._apply_filters(product, filters):
                    continue

            product['search_score'] = float(score)
            product['bm25_score'] = float(bm25_normalized.get(idx, 0))
            product['cosine_score'] = float(cosine_normalized.get(idx, 0))

            # Remove MongoDB _id for clean output
            product.pop('_id', None)

            results.append(product)

        print(f" Found {len(results)} results")
        return results

    def _apply_filters(self, product: Dict, filters: Dict) -> bool:
        """Apply filters to product"""

        # Brand filter
        if 'brand_id' in filters:
            if product.get('brand_id') != filters['brand_id']:
                return False

        # Price range filter
        if 'min_price' in filters:
            price = product.get('price_min', 0)
            if price < filters['min_price']:
                return False

        if 'max_price' in filters:
            price = product.get('price_min', float('inf'))
            if price > filters['max_price']:
                return False

        # Product type filter
        if 'product_type' in filters:
            if product.get('product_type') != filters['product_type']:
                return False

        # Availability filter
        if 'available_only' in filters and filters['available_only']:
            if not product.get('available', False):
                return False

        return True

    def search_with_insights(
            self,
            query: str,
            top_k: int = 10
    ) -> Dict:
        """
        Search with additional recommendations and insights
        """
        # Perform hybrid search
        results = self.hybrid_search(query, top_k=top_k)

        # Extract insights
        brands_found = {}
        price_range = {'min': float('inf'), 'max': 0}
        product_types = {}

        for product in results:
            # Brand distribution
            brand = product.get('brand_name', 'Unknown')
            brands_found[brand] = brands_found.get(brand, 0) + 1

            # Price range
            price = product.get('price_min', 0)
            if price > 0:
                price_range['min'] = min(price_range['min'], price)
                price_range['max'] = max(price_range['max'], price)

            # Product type distribution
            ptype = product.get('product_type', 'Unknown')
            product_types[ptype] = product_types.get(ptype, 0) + 1

        return {
            'query': query,
            'total_results': len(results),
            'products': results,
            'insights': {
                'brands': brands_found,
                'price_range': price_range if price_range['min'] != float('inf') else None,
                'product_types': product_types
            }
        }

    def close(self):
        """Close database connection"""
        self.client.close()


# ============================================
# DEMO & TESTING
# ============================================
def demo_search():


    # Initialize search engine
    search_engine = VastrHybridSearch()

    # Test queries
    test_queries = [
        "embroidered lawn suit",
        "summer collection women",
        "formal dress",
        "casual wear",
        "bridal collection"
    ]

    print("\n" + "=" * 60)
    print("TESTING HYBRID SEARCH")
    print("=" * 60)

    for query in test_queries:
        results = search_engine.search_with_insights(query, top_k=5)

        print(f"\n Query: '{query}'")
        print(f" Found: {results['total_results']} results")

        print(f"\n Top 5 Results:")
        for i, product in enumerate(results['products'][:5], 1):
            print(f"\n   {i}. {product.get('title', 'N/A')[:60]}")
            print(f"      Brand: {product.get('brand_name')}")
            print(f"      Price: PKR {product.get('price_min', 0):,.2f}")
            print(
                f"      Score: {product.get('search_score', 0):.3f} (BM25: {product.get('bm25_score', 0):.3f}, Cosine: {product.get('cosine_score', 0):.3f})")

        print(f"\nInsights:")
        insights = results['insights']
        print(f"   Brands: {', '.join(f'{b}({c})' for b, c in list(insights['brands'].items())[:3])}")
        if insights['price_range']:
            print(f"   Price Range: PKR {insights['price_range']['min']:,.0f} - {insights['price_range']['max']:,.0f}")

        print("\n" + "-" * 60)

    # Close connection
    search_engine.close()


# ============================================
# MAIN EXECUTION
# ============================================
if __name__ == "__main__":
    demo_search()

    print("\n Hybrid Search Engine Ready!")
    print("\n Usage Example:")
