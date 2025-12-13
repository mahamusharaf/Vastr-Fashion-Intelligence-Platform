"""
regenerate_embeddings.py
Generates image_search_data.npz with CORRECT MongoDB _id strings
Run this whenever your products change or image search stops working
"""

import numpy as np
import os
import sys
import time
from tqdm import tqdm
from PIL import Image
from io import BytesIO
import requests
import torch
from transformers import ViTImageProcessor, ViTModel

# Add current path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from database import get_products_collection
from bson import ObjectId


def get_first_image_url(product):
    url = product.get("image_url")
    if url and isinstance(url, str) and url.strip().startswith(("http://", "https://")):
        return url.strip()

    images = product.get("images") or []
    for img in images:
        src = img.get("src") if isinstance(img, dict) else None
        if src and isinstance(src, str) and src.strip().startswith(("http://", "https://")):
            return src.strip()
    return None


def download_image(url, timeout=15):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'image/*,*/*;q=0.8',
        'Referer': 'https://www.google.com/'
    }
    try:
        r = requests.get(url, headers=headers, timeout=timeout, stream=True)
        r.raise_for_status()
        if 'image' not in r.headers.get('content-type', '').lower():
            return None, "Not an image"
        img = Image.open(BytesIO(r.content))
        return img.convert("RGB"), None
    except Exception as e:
        return None, str(e)[:60]


def preprocess_image(img, max_size=800):
    if img.mode != "RGB":
        img = img.convert("RGB")
    if max(img.size) > max_size:
        img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
    return img


def main():
    print("\n" + "="*70)
    print("REGENERATING IMAGE EMBEDDINGS WITH CORRECT PRODUCT IDs")
    print("="*70 + "\n")

    # Load model
    print("Loading ViT model (google/vit-base-patch16-224-in21k)...")
    processor = ViTImageProcessor.from_pretrained("google/vit-base-patch16-224-in21k")
    model = ViTModel.from_pretrained("google/vit-base-patch16-224-in21k")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    model.eval()
    print(f"Model loaded on {device}\n")

    # Connect & fetch products
    collection = get_products_collection()
    products = list(collection.find({
        "$or": [
            {"image_url": {"$exists": True, "$ne": None}},
            {"images.0.src": {"$exists": True}}
        ]
    }))

    print(f"Found {len(products)} products with images\n")
    if len(products) == 0:
        print("No products found! Check your database.")
        return

    embeddings = []
    product_ids = []
    failures = {}

    print("Processing images...\n")
    for product in tqdm(products, desc="Generating embeddings"):
        url = get_first_image_url(product)
        if not url:
            failures["No URL"] = failures.get("No URL", 0) + 1
            continue

        img, err = download_image(url)
        if not img:
            failures[err or "Download failed"] = failures.get(err or "Download failed", 0) + 1
            continue

        try:
            img = preprocess_image(img)
            inputs = processor(images=img, return_tensors="pt").to(device)
            with torch.no_grad():
                outputs = model(**inputs)
                emb = outputs.last_hidden_state[:, 0].cpu().numpy().flatten()
                emb = emb / (np.linalg.norm(emb) + 1e-10)

            embeddings.append(emb)
            product_ids.append(str(product["_id"]))   # CRITICAL: Save as string!
        except Exception as e:
            failures[f"Error: {str(e)[:40]}"] = failures.get(f"Error: {str(e)[:40]}", 0) + 1

    # Save
    if len(embeddings) < 50:
        print(f"\nOnly {len(embeddings)} embeddings generated — too few!")
        return

    # Backup old file
    if os.path.exists("image_search_data.npz"):
        os.rename("image_search_data.npz", "image_search_data.npz.backup")

    np.savez_compressed(
        "image_search_data.npz",
        embeddings=np.array(embeddings, dtype=np.float32),
        product_ids=np.array(product_ids, dtype=object)
    )

    size_mb = os.path.getsize("image_search_data.npz") / (1024*1024)
    print(f"\nSUCCESS! Saved {len(embeddings)} embeddings")
    print(f"File: image_search_data.npz ({size_mb:.2f} MB)")

    # Verify IDs match DB
    print("\nVerifying IDs match database...")
    test_ids = product_ids[:10]
    matches = sum(1 for pid in test_ids if collection.find_one({"_id": ObjectId(pid)}))
    print(f"{matches}/10 sample IDs exist in DB → {'PERFECT' if matches == 10 else 'CHECK DB'}")

    if matches == 10:
        print("\n" + "SUCCESS!"*8)
        print("IMAGE SEARCH IS NOW FIXED!")
        print("\nNext: Restart your FastAPI server")
        print("      Then test uploading an image — it WILL work!")
        print("SUCCESS!"*8 + "\n")
    else:
        print("Some IDs don't match. Did you delete/reimport products recently?")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nCancelled by user")
    except Exception as e:
        import traceback
        traceback.print_exc()