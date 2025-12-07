# routes/image_search.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from PIL import Image
import base64
import io
import numpy as np
import torch
from transformers import ViTImageProcessor, ViTModel
from sklearn.metrics.pairwise import cosine_similarity
import os

router = APIRouter(prefix="/api/v1/search", tags=["Image Search"])

# -------------------
# Global variables
# -------------------
_VIT_MODEL = None
_VIT_PROCESSOR = None
_DEVICE = None
_EMBEDDINGS = None
_PRODUCT_IDS = None

# -------------------
# Request model
# -------------------
class ImageSearchRequest(BaseModel):
    image: str  # base64 string
    limit: int = 24

# -------------------
# Load model
# -------------------
def load_model():
    global _VIT_MODEL, _VIT_PROCESSOR, _DEVICE
    if _VIT_MODEL:
        return True
    MODEL_NAME = "google/vit-base-patch16-224-in21k"
    try:
        _VIT_PROCESSOR = ViTImageProcessor.from_pretrained(MODEL_NAME, cache_dir="./image_cache")
        _VIT_MODEL = ViTModel.from_pretrained(MODEL_NAME, cache_dir="./image_cache")
        _DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        _VIT_MODEL.to(_DEVICE)
        _VIT_MODEL.eval()
        print("ViT model loaded successfully")
        return True
    except Exception as e:
        print(f"Failed to load model: {e}")
        return False

# -------------------
# Load embeddings from MULTIPLE files
# -------------------
def load_embeddings():
    global _EMBEDDINGS, _PRODUCT_IDS
    
    npz_files = [
        "image_search_data_mergeduse.npz",
        "image_search_data_first1326.npz"
    ]
    
    all_embeddings = []
    all_product_ids = []
    loaded_count = 0
    
    print("\n" + "=" * 70)
    print("  Loading Embeddings from Multiple Files")
    print("=" * 70)
    
    for npz_file in npz_files:
        if not os.path.exists(npz_file):
            print(f"Warning: {npz_file} not found - skipping")
            continue
        
        try:
            print(f"\nLoading: {npz_file}")
            data = np.load(npz_file, allow_pickle=True)
            embeddings = data["embeddings"].astype(np.float32)
            product_ids = data["product_ids"].tolist()
            
            print(f"   Loaded {len(product_ids):,} products")
            
            all_embeddings.append(embeddings)
            all_product_ids.extend(product_ids)
            loaded_count += 1
            
        except Exception as e:
            print(f"   Failed to load {npz_file}: {e}")
            continue
    
    if loaded_count == 0:
        print("\nNo embeddings loaded!")
        return False
    
    print(f"\nCombining embeddings from {loaded_count} files...")
    _EMBEDDINGS = np.vstack(all_embeddings)
    _PRODUCT_IDS = all_product_ids

    # FIX: Force normalization (this fixed your Nishat issue)
    print("Forcing L2 normalization on all embeddings...")
    norms = np.linalg.norm(_EMBEDDINGS, axis=1, keepdims=True)
    _EMBEDDINGS = _EMBEDDINGS / np.clip(norms, a_min=1e-10, a_max=None)

    # THIS IS THE ONLY NEW PART – TELLS YOU IF NISHAT IS IN FIRST 1326
    print("\n" + "CHECKING: Are first 1326 products really Nishat + Ethnic?")
    if len(_PRODUCT_IDS) >= 1326:
        print(f"   First 10 IDs  → {_PRODUCT_IDS[:10]}")
        print(f"   ID #1000      → {_PRODUCT_IDS[999]}")
        print(f"   ID #1326      → {_PRODUCT_IDS[1325]}")
        print(f"   ID #1327      → {_PRODUCT_IDS[1326] if len(_PRODUCT_IDS) > 1326 else '(end)'}")
        if any("nishat" in str(x).lower() or "ethnic" in str(x).lower() for x in _PRODUCT_IDS[:1326]):
            print("   NISHAT + ETHNIC ARE IN THE FIRST 1326!")
        else:
            print("   WARNING: First 1326 do NOT look like Nishat/Ethnic!")
    else:
        print(f"   Only {len(_PRODUCT_IDS)} total products – something is wrong!")
    print("="*80 + "\n")
    # END OF DEBUG BLOCK

    unique_ids = set(_PRODUCT_IDS)
    if len(unique_ids) < len(_PRODUCT_IDS):
        duplicates = len(_PRODUCT_IDS) - len(unique_ids)
        print(f"   Warning: Found {duplicates} duplicate product IDs")
    else:
        print(f"   All product IDs are unique")
    
    print(f"  TOTAL LOADED: {len(_PRODUCT_IDS):,} products")
    print(f"  Embedding shape: {_EMBEDDINGS.shape}")
    print(f"  Ready for image search!")
    print(f"{'=' * 70}\n")
    
    return True

@router.post("/image")
async def search_by_image(req: ImageSearchRequest):
    if _EMBEDDINGS is None or _PRODUCT_IDS is None or len(_EMBEDDINGS) == 0:
        raise HTTPException(503, "Image search not ready – embeddings missing")
    
    emb = get_embedding_from_base64(req.image)
    if emb is None:
        raise HTTPException(500, "Failed to process image")

    sims = cosine_similarity(emb.reshape(1, -1), _EMBEDDINGS)[0]
    top_idx = np.argsort(sims)[::-1][:req.limit]
    results = [{"product_id": str(_PRODUCT_IDS[i]), "similarity": float(sims[i])} for i in top_idx]
    
    return {"results": results}

# -------------------
# Helpers
# -------------------
def preprocess_image(image: Image.Image) -> Image.Image:
    if image.mode != "RGB":
        image = image.convert("RGB")
    max_size = 800
    if max(image.size) > max_size:
        image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
    return image

def get_embedding_from_base64(base64_str: str):
    if not _VIT_MODEL:
        return None
    try:
        img_data = base64.b64decode(base64_str)
        img = Image.open(io.BytesIO(img_data))
        img = preprocess_image(img)
        inputs = _VIT_PROCESSOR(images=img, return_tensors="pt")
        inputs = {k: v.to(_DEVICE) for k, v in inputs.items()}
        with torch.no_grad():
            outputs = _VIT_MODEL(**inputs)
            emb = outputs.last_hidden_state[:, 0, :].cpu().numpy().flatten()
            emb /= np.linalg.norm(emb) + 1e-10
            return emb
    except Exception as e:
        print(f"Embedding extraction failed: {e}")
        return None

# -------------------
# Auto-initialize
# -------------------
load_model()
load_embeddings()

# -------------------
# Rest of your original code (unchanged)
# -------------------
if __name__ == "__main__":
    print("\n=== VASTR Image Search Standalone Test ===\n")
    if load_model() and load_embeddings():
        print("System ready. Number of products:", len(_PRODUCT_IDS))
        test_image_path = "test.jpg"
        if os.path.exists(test_image_path):
            with open(test_image_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
                emb = get_embedding_from_base64(b64)
                if emb is not None:
                    results = np.dot(_EMBEDDINGS, emb)
                    top = np.argsort(results)[::-1][:10]
                    print("Top 10 similar product IDs:", [str(_PRODUCT_IDS[i]) for i in top])
        else:
            print("No test image found.")
    else:
        print("System not ready.")

import requests
from io import BytesIO

def get_embedding_from_url(url: str):
    if not _VIT_MODEL:
        return None
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        img = Image.open(BytesIO(response.content))
        img = preprocess_image(img)
        inputs = _VIT_PROCESSOR(images=img, return_tensors="pt")
        inputs = {k: v.to(_DEVICE) for k, v in inputs.items()}
        with torch.no_grad():
            outputs = _VIT_MODEL(**inputs)
            emb = outputs.last_hidden_state[:, 0, :].cpu().numpy().flatten()
            emb /= np.linalg.norm(emb) + 1e-10
            return emb
    except Exception as e:
        print(f"Failed to get embedding from {url}: {e}")
        return None