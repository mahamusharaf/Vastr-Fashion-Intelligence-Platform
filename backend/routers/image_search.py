from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from PIL import Image
import base64, io, numpy as np, torch, os, re
from transformers import ViTImageProcessor, ViTModel
from sklearn.metrics.pairwise import cosine_similarity
from database import get_products_collection
from bson import ObjectId

router = APIRouter(prefix="/api/v1/search", tags=["Image Search"])

# -------------------
# Globals
# -------------------
_VIT_MODEL = None
_VIT_PROCESSOR = None
_DEVICE = None
_EMBEDDINGS = None
_PRODUCT_IDS = None


class ImageSearchRequest(BaseModel):
    image: str  # base64
    limit: int = 24


# -------------------
# Load ViT model
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
        print("✓ ViT model loaded successfully")
        return True
    except Exception as e:
        print(f"✗ Failed to load model: {e}")
        return False


# -------------------
# Load embeddings
# -------------------
def load_embeddings():
    global _EMBEDDINGS, _PRODUCT_IDS

    # Try main file first, then backup
    possible_files = ["image_search_data.npz", "image_search_data.npz.backup"]

    for f in possible_files:
        if os.path.exists(f):
            try:
                data = np.load(f, allow_pickle=True)
                _EMBEDDINGS = data["embeddings"].astype(np.float32)
                _PRODUCT_IDS = data["product_ids"].tolist()
                print(f"✓ Loaded {_EMBEDDINGS.shape[0]} embeddings from {f}")
                return True
            except Exception as e:
                print(f"✗ Failed to load {f}: {e}")
                continue

    print("✗ No embeddings file found (tried: image_search_data.npz, image_search_data.npz.backup)")
    return False


# -------------------
# Image preprocessing & embedding
# -------------------
def preprocess_image(image: Image.Image):
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
        print(f"✗ Embedding extraction failed: {e}")
        return None


# -------------------
# Helper: Get product by ID with fallback
# -------------------
def get_product_by_id(collection, product_id):
    """Try multiple ID formats to find the product"""
    # Try as ObjectId first (most common)
    try:
        if isinstance(product_id, str) and len(product_id) == 24:
            doc = collection.find_one({"_id": ObjectId(product_id)})
            if doc:
                return doc
    except Exception as e:
        print(f"  ⚠ ObjectId lookup failed for {product_id}: {e}")

    # Try as string _id
    try:
        doc = collection.find_one({"_id": str(product_id)})
        if doc:
            return doc
    except:
        pass

    return None


# -------------------
# Helper: Extract product fields safely
# -------------------
def extract_product_data(doc):
    """Extract product data matching your MongoDB schema"""
    if not doc:
        return None

    # Get fields matching your schema
    name = doc.get("title", "Unnamed Product")
    price = doc.get("price_min", 0)
    link = doc.get("url", "#")
    brand = doc.get("brand_name", "")

    # Get images array - your DB stores images as objects with "src" field
    images = doc.get("images", [])
    image = None

    if images and isinstance(images, list) and len(images) > 0:
        # Get the first image from the array
        first_image = images[0]

        # Images are objects with "src" field
        if isinstance(first_image, dict):
            image = first_image.get("src")
        elif isinstance(first_image, str):
            # Fallback if it's a string
            image = first_image

    # Clean up image URL if it exists
    if image:
        image = str(image).strip()

        # Your Shopify URLs are missing the file extension - add it
        # Check if URL is missing extension
        if not re.search(r'\.(jpg|jpeg|png|gif|webp)$', image, re.IGNORECASE):
            # Add .jpg extension (Shopify default)
            image = image + '.jpg'

        # Ensure it starts with http:// or https://
        if not image.startswith(('http://', 'https://')):
            image = None

    # If no valid image, use a placeholder
    if not image:
        image = "https://via.placeholder.com/400x600/cccccc/666666?text=No+Image"

    return {
        "name": f"{brand} - {name}" if brand else str(name),
        "price": int(price) if isinstance(price, (int, float)) else 0,
        "image": image,
        "link": str(link)
    }


# -------------------
# API endpoint
# -------------------
@router.post("/image")
async def search_by_image(req: ImageSearchRequest):
    # Check if embeddings are loaded
    if _EMBEDDINGS is None or _PRODUCT_IDS is None:
        raise HTTPException(
            status_code=503,
            detail="Image search not initialized - embeddings file missing"
        )

    # Check if model is loaded
    if not _VIT_MODEL:
        raise HTTPException(
            status_code=503,
            detail="Image search not initialized - model not loaded"
        )

    # Get embedding from uploaded image
    print("📸 Processing uploaded image...")
    emb = get_embedding_from_base64(req.image)
    if emb is None:
        raise HTTPException(
            status_code=500,
            detail="Failed to process image - invalid format or corrupted"
        )

    # Calculate similarities
    print("🔍 Searching for similar products...")
    sims = cosine_similarity(emb.reshape(1, -1), _EMBEDDINGS)[0]
    top_idx = np.argsort(sims)[::-1][:req.limit]

    # Get product collection
    product_collection = get_products_collection()

    # Fetch matching products
    results = []
    for i in top_idx:
        pid = _PRODUCT_IDS[i]
        similarity = float(sims[i])

        # Try to find product in database
        doc = get_product_by_id(product_collection, pid)

        if doc:
            product_data = extract_product_data(doc)
            if product_data:
                product_data["similarity"] = round(similarity * 100, 2)  # Add similarity score
                results.append(product_data)
                print(f"✓ Found: {product_data['name'][:50]}... (similarity: {product_data['similarity']}%)")
        else:
            print(f"✗ Product not found in DB: {pid}")

    print(f"✓ Returning {len(results)} results")

    if not results:
        return {
            "results": [],
            "message": "No matching products found in database",
            "total": 0
        }

    return {
        "results": results,
        "total": len(results)
    }


# -------------------
# Debug Endpoints
# -------------------
@router.get("/debug/status")
async def debug_status():
    """Quick status check"""
    return {
        "model_loaded": _VIT_MODEL is not None,
        "embeddings_loaded": _EMBEDDINGS is not None,
        "embedding_count": len(_PRODUCT_IDS) if _PRODUCT_IDS else 0,
        "db_products": get_products_collection().count_documents({})
    }


@router.get("/debug/first-product")
async def debug_first_product():
    """Show the FIRST product in database with all its fields"""
    product_collection = get_products_collection()

    # Get the very first product
    doc = product_collection.find_one()

    if not doc:
        return {"error": "No products in database"}

    # Convert to dict for JSON
    doc_dict = {}
    for key, value in doc.items():
        if key == "_id":
            doc_dict[key] = str(value)
        else:
            doc_dict[key] = value

    return {
        "total_products": product_collection.count_documents({}),
        "all_fields": list(doc.keys()),
        "raw_document": doc_dict
    }


@router.get("/debug/raw-product/{product_id}")
async def debug_raw_product(product_id: str):
    """Show raw MongoDB document for a specific product"""
    product_collection = get_products_collection()

    # Try to find the product
    doc = get_product_by_id(product_collection, product_id)

    if not doc:
        return {"error": "Product not found", "tried_id": product_id}

    # Convert ObjectId to string for JSON serialization
    doc_dict = {}
    for key, value in doc.items():
        if key == "_id":
            doc_dict[key] = str(value)
        else:
            doc_dict[key] = value

    return {
        "product_id": product_id,
        "found": True,
        "all_fields": list(doc.keys()),
        "raw_document": doc_dict
    }


@router.get("/debug/test-search")
async def debug_test_search():
    """Test search with first embedding"""
    if _EMBEDDINGS is None or _PRODUCT_IDS is None:
        return {"error": "Embeddings not loaded"}

    product_collection = get_products_collection()

    # Use first embedding as test
    test_emb = _EMBEDDINGS[0]
    sims = cosine_similarity(test_emb.reshape(1, -1), _EMBEDDINGS)[0]
    top_idx = np.argsort(sims)[::-1][:10]

    results = []
    for i in top_idx:
        pid = _PRODUCT_IDS[i]
        doc = get_product_by_id(product_collection, pid)

        if doc:
            product_data = extract_product_data(doc)
            results.append({
                "rank": len(results) + 1,
                "similarity": float(sims[i]),
                "embedding_id": str(pid),
                "found_in_db": True,
                "product_name": doc.get("title", "N/A"),
                "image_url": product_data["image"] if product_data else None
            })
        else:
            results.append({
                "rank": len(results) + 1,
                "similarity": float(sims[i]),
                "embedding_id": str(pid),
                "found_in_db": False
            })

    return {
        "test_embedding_index": 0,
        "test_embedding_id": str(_PRODUCT_IDS[0]),
        "top_10_results": results,
        "successful_matches": sum(1 for r in results if r["found_in_db"])
    }


# -------------------
# Initialize on module load - THIS IS CRITICAL!
# -------------------
print("\n" + "=" * 50)
print("🔧 Initializing Image Search Module...")
print("=" * 50)

model_loaded = load_model()
embeddings_loaded = load_embeddings()

if model_loaded and embeddings_loaded:
    print("✓ Image Search Ready!")
else:
    print("✗ Image Search NOT Ready - check errors above")

print("=" * 50 + "\n")