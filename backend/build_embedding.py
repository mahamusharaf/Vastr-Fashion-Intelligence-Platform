# build_nishat_and_ethnic_embeddings_fixed.py
# This version shows you EXACTLY why images fail

import os
import numpy as np
import requests
from PIL import Image
from io import BytesIO
from transformers import ViTImageProcessor, ViTModel
import torch
from pymongo import MongoClient
from tqdm import tqdm
import time

# ==================== CONFIG ====================
MONGODB_URI = "mongodb://localhost:27017"
DB_NAME     = "vastr"
COLLECTION  = "products"
OUTPUT_FILE = "image_search_data_first1326.npz"
TOTAL_LIMIT = 1326
# ===============================================

print("Loading ViT model...")
processor = ViTImageProcessor.from_pretrained("google/vit-base-patch16-224-in21k")
model = ViTModel.from_pretrained("google/vit-base-patch16-224-in21k")
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)
model.eval()

def download_and_embed(url):
    try:
        print(f"   Trying → {url[:80]}...", end="")
        response = requests.get(url, timeout=20, headers={'User-Agent': 'Mozilla/5.0'})
        if response.status_code != 200:
            print(f" HTTP {response.status_code}")
            return None
        img = Image.open(BytesIO(response.content)).convert("RGB")
        inputs = processor(images=img, return_tensors="pt")
        inputs = {k: v.to(device) for k, v in inputs.items()}
        with torch.no_grad():
            emb = model(**inputs).last_hidden_state[:, 0, :].cpu().numpy().flatten()
            emb = emb / (np.linalg.norm(emb) + 1e-10)
        print(" SUCCESS")
        return emb
    except Exception as e:
        print(f" FAILED → {e}")
        return None

# Connect & fetch
client = MongoClient(MONGODB_URI)
coll = client[DB_NAME][COLLECTION]

products = list(coll.find({
    "brand_name": {"$in": ["Nishat Linen", "Ethnic"]}
}).sort("_id", 1).limit(TOTAL_LIMIT))

print(f"Found {len(products)} Nishat + Ethnic products")

embeddings = []
product_ids = []

for prod in tqdm(products[:50]):  # ← only first 50 to test fast
    images = prod.get("images", [])
    if not images:
        continue
    emb = download_and_embed(images[0])
    if emb is not None:
        embeddings.append(emb)
        product_ids.append(str(prod["_id"]))
    time.sleep(0.1)

print(f"\nSuccessfully embedded: {len(embeddings)} / 50 tested")
if len(embeddings) > 0:
    np.savez_compressed(OUTPUT_FILE, embeddings=np.array(embeddings), product_ids=np.array(product_ids))
    print(f"Saved test file with {len(embeddings)} products")
else:
    print("ZERO images worked → internet is blocked or CDN blocks your IP")