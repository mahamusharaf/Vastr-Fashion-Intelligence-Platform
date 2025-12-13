"""
Quick diagnostic script - run this from your backend folder
Usage: python quick_diagnostic.py
"""

import numpy as np
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import get_products_collection
from bson import ObjectId

print("\n" + "=" * 60)
print("🔍 IMAGE SEARCH DIAGNOSTIC")
print("=" * 60 + "\n")

# Load embeddings
try:
    data = np.load("image_search_data.npz", allow_pickle=True)
    embeddings = data["embeddings"]
    product_ids = data["product_ids"]
    print(f"✓ Loaded {len(product_ids)} embeddings from file")
    print(f"  Embeddings shape: {embeddings.shape}")
except Exception as e:
    print(f"✗ Failed to load embeddings: {e}")
    print(f"  Current directory: {os.getcwd()}")
    print(f"  Looking for: image_search_data.npz")
    exit(1)

# Connect to database
try:
    collection = get_products_collection()
    db_count = collection.count_documents({})
    print(f"✓ Connected to database: {db_count} products\n")
except Exception as e:
    print(f"✗ Failed to connect to database: {e}")
    exit(1)

# Check ID format
print("📊 ID FORMAT ANALYSIS")
print("-" * 60)

sample_embedding_ids = product_ids[:5]
print("\nSample embedding IDs:")
for i, pid in enumerate(sample_embedding_ids):
    print(f"  [{i}] '{pid}' (type: {type(pid).__name__}, len: {len(str(pid))})")

print("\nSample database IDs:")
for i, doc in enumerate(collection.find().limit(5)):
    print(f"  [{i}] '{doc['_id']}' (type: {type(doc['_id']).__name__})")

# Test matching
print("\n" + "-" * 60)
print("🔍 MATCHING TEST")
print("-" * 60 + "\n")

matches = 0
mismatches = 0
match_examples = []
mismatch_examples = []

print("Testing first 50 embedding IDs against database...\n")

for i, pid in enumerate(product_ids[:50]):
    # Try different ID formats
    found = False
    found_method = None

    # Method 1: Try as ObjectId
    try:
        if len(str(pid)) == 24:
            doc = collection.find_one({"_id": ObjectId(str(pid))})
            if doc:
                found = True
                found_method = "ObjectId"
    except Exception as e:
        pass

    # Method 2: Try as string
    if not found:
        try:
            doc = collection.find_one({"_id": str(pid)})
            if doc:
                found = True
                found_method = "String"
        except:
            pass

    # Method 3: Try as int
    if not found:
        try:
            doc = collection.find_one({"_id": int(pid)})
            if doc:
                found = True
                found_method = "Integer"
        except:
            pass

    # Method 4: Try product_id field
    if not found:
        try:
            doc = collection.find_one({"product_id": str(pid)})
            if doc:
                found = True
                found_method = "product_id field"
        except:
            pass

    if found:
        matches += 1
        if len(match_examples) < 3:
            match_examples.append(f"  ✓ '{pid}' → {doc.get('title', 'N/A')[:40]} (via {found_method})")
    else:
        mismatches += 1
        if len(mismatch_examples) < 3:
            mismatch_examples.append(f"  ✗ '{pid}'")

# Show examples
if match_examples:
    print("Sample MATCHES:")
    for ex in match_examples:
        print(ex)
    print()

if mismatch_examples:
    print("Sample MISMATCHES:")
    for ex in mismatch_examples:
        print(ex)
    print()

print(f"{'=' * 60}")
print(f"RESULTS: {matches} matches, {mismatches} mismatches out of 50 tested")
print(f"Match rate: {(matches / 50) * 100:.1f}%")
print(f"{'=' * 60}\n")

if matches == 0:
    print("❌ CRITICAL PROBLEM: No matches found!")
    print()
    print("DIAGNOSIS:")
    print("  → Your embeddings file uses DIFFERENT IDs than your database")
    print("  → The embedding IDs don't correspond to any products in MongoDB")
    print()
    print("SOLUTION:")
    print("  1. You MUST regenerate the embeddings file")
    print("  2. Run: python regenerate_embeddings.py")
    print("  3. Then restart your server")
    print()
elif matches < 25:
    print("⚠️  WARNING: Low match rate!")
    print()
    print("DIAGNOSIS:")
    print("  → Some IDs match but most don't")
    print("  → Database may have been partially reimported")
    print()
    print("SOLUTION:")
    print("  → Regenerate embeddings for consistency")
    print("  → Run: python regenerate_embeddings.py")
    print()
else:
    print("✅ GOOD: IDs are matching!")
    print()
    print("DIAGNOSIS:")
    print("  → The ID matching is working fine")
    print("  → The issue is likely in the search logic or image processing")
    print()
    print("NEXT STEPS:")
    print("  → Add debug logging to the /image endpoint")
    print("  → Check if embeddings are being generated correctly from uploaded images")
    print()

print()