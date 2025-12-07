"""
Build embeddings for your MongoDB products - Enhanced Version
Run this ONCE: python build_embeddings.py
"""

from pymongo import MongoClient
from image_search import load_model, get_embedding_from_url
import numpy as np
from datetime import datetime
import time
import json
from pathlib import Path

# Your MongoDB settings
MONGO_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "vastr_fashion_db"
OUTPUT_FILE = "image_search_data.npz"
CHECKPOINT_FILE = "embedding_checkpoint.json"

def save_checkpoint(processed_ids, embeddings, product_ids):
    """Save progress checkpoint"""
    checkpoint = {
        'processed': len(processed_ids),
        'timestamp': datetime.now().isoformat(),
        'processed_ids': list(processed_ids)
    }
    
    with open(CHECKPOINT_FILE, 'w') as f:
        json.dump(checkpoint, f)
    
    # Save partial results
    if embeddings:
        np.savez(
            f"{OUTPUT_FILE}.partial",
            embeddings=np.array(embeddings),
            product_ids=np.array(product_ids),
            created_at=datetime.now().isoformat()
        )

def load_checkpoint():
    """Load previous progress if exists"""
    if Path(CHECKPOINT_FILE).exists():
        try:
            with open(CHECKPOINT_FILE, 'r') as f:
                data = json.load(f)
            print(f"📂 Checkpoint found: {data['processed']} products already processed")
            return data
        except Exception as e:
            print(f"⚠️  Could not load checkpoint: {e}")
    return None

def build_embeddings(limit=None, resume=True, batch_size=8):
    """
    Build embeddings for all products
    
    Args:
        limit: Max number of products (None = all)
        resume: Resume from checkpoint if available
        batch_size: Save checkpoint after this many products
    """
    
    print("=" * 70)
    print("  VASTR - Building Image Search Embeddings (Enhanced)")
    print("=" * 70)
    
    # Connect MongoDB
    print("\n📦 Connecting to MongoDB...")
    client = MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]
    products_collection = db['products']
    
    total_count = products_collection.count_documents({})
    print(f"   Total products in database: {total_count:,}")
    
    # Load checkpoint if resuming
    checkpoint = None
    processed_ids = set()
    
    if resume:
        checkpoint = load_checkpoint()
        if checkpoint:
            processed_ids = set(checkpoint['processed_ids'])
    
    # Get products
    query = {}
    if processed_ids:
        from bson import ObjectId
        # Convert string IDs back to ObjectId for query
        processed_object_ids = []
        for pid in processed_ids:
            try:
                processed_object_ids.append(ObjectId(pid))
            except:
                processed_object_ids.append(pid)
        query['_id'] = {'$nin': processed_object_ids}
    
    if limit:
        print(f"   Processing: {limit} products (test mode)")
        products = list(products_collection.find(query).limit(limit))
    else:
        print(f"   Processing: All remaining products")
        products = list(products_collection.find(query))
    
    print(f"   Found: {len(products)} products to process")
    
    if checkpoint:
        print(f"   Resuming from: {len(processed_ids)} already processed\n")
    else:
        print()
    
    # Load model
    print("🤖 Loading AI model...")
    if not load_model():
        print("❌ Could not load model")
        client.close()
        return
    print("   Model ready!\n")
    
    # Process
    embeddings = []
    product_ids = []
    failed = []
    
    print("🔨 Generating embeddings...")
    print(f"   Checkpoint saves every {batch_size} products")
    print("   This will take time. Please be patient...\n")
    
    start_time = time.time()
    
    try:
        for i, product in enumerate(products):
            try:
                # Progress update
                if i % 10 == 0 and i > 0:
                    elapsed = time.time() - start_time
                    rate = i / elapsed
                    remaining = len(products) - i
                    eta_seconds = remaining / rate if rate > 0 else 0
                    eta_minutes = eta_seconds / 60
                    
                    print(f"   Progress: {i}/{len(products)} | "
                          f"Success: {len(embeddings)} | "
                          f"Failed: {len(failed)} | "
                          f"Rate: {rate:.1f}/s | "
                          f"ETA: {eta_minutes:.1f}m")
                
                product_id = str(product['_id'])
                
                # Get first image URL
                images = product.get('images', [])
                if not images:
                    failed.append({
                        'id': product_id,
                        'reason': 'No images'
                    })
                    continue
                
                # Handle different image formats
                if isinstance(images[0], dict):
                    image_url = images[0].get('url') or images[0].get('src')
                elif isinstance(images[0], str):
                    image_url = images[0]
                else:
                    failed.append({
                        'id': product_id,
                        'reason': 'Invalid image format'
                    })
                    continue
                
                if not image_url:
                    failed.append({
                        'id': product_id,
                        'reason': 'No image URL'
                    })
                    continue
                
                # Get embedding
                embedding = get_embedding_from_url(image_url)
                
                if embedding is not None:
                    embeddings.append(embedding)
                    product_ids.append(product_id)
                    processed_ids.add(product_id)
                else:
                    failed.append({
                        'id': product_id,
                        'reason': 'Embedding extraction failed',
                        'url': image_url[:100]
                    })
                
                # Save checkpoint
                if (i + 1) % batch_size == 0:
                    save_checkpoint(processed_ids, embeddings, product_ids)
                    print(f"   💾 Checkpoint saved ({len(embeddings)} embeddings)")
            
            except Exception as e:
                failed.append({
                    'id': str(product.get('_id', 'unknown')),
                    'reason': str(e)
                })
        
        # Final progress
        print(f"\n   Final: {len(products)}/{len(products)} | "
              f"Success: {len(embeddings)} | "
              f"Failed: {len(failed)}")
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user!")
        print("   Progress has been saved. Run again with resume to continue.")
        save_checkpoint(processed_ids, embeddings, product_ids)
        client.close()
        return
    
    # Save final results
    if embeddings:
        embeddings_array = np.array(embeddings)
        
        # Save main file
        np.savez(
            OUTPUT_FILE,
            embeddings=embeddings_array,
            product_ids=np.array(product_ids),
            created_at=datetime.now().isoformat(),
            version='2.0'
        )
        
        elapsed_time = time.time() - start_time
        
        print(f"\n{'=' * 70}")
        print("✅ SUCCESS - Embeddings Saved!")
        print(f"{'=' * 70}")
        print(f"   Output file: {OUTPUT_FILE}")
        print(f"   Total embeddings: {len(product_ids):,}")
        print(f"   Embedding shape: {embeddings_array.shape}")
        print(f"   Success rate: {len(product_ids)/(len(product_ids)+len(failed))*100:.1f}%")
        print(f"   Failed: {len(failed):,}")
        print(f"   Time taken: {elapsed_time/60:.1f} minutes")
        print(f"   Speed: {len(product_ids)/elapsed_time:.1f} products/second")
        
        # Save failure log
        if failed:
            failure_log = f"embedding_failures_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(failure_log, 'w') as f:
                json.dump(failed, f, indent=2)
            
            print(f"\n   Failure log: {failure_log}")
            print(f"   Sample failures:")
            for fail in failed[:5]:
                reason = fail.get('reason', 'Unknown')
                print(f"      - {fail['id']}: {reason}")
            if len(failed) > 5:
                print(f"      ... and {len(failed) - 5} more")
        
        # Cleanup
        if Path(CHECKPOINT_FILE).exists():
            Path(CHECKPOINT_FILE).unlink()
            print("\n   Checkpoint file removed (build complete)")
        
        partial_file = Path(f"{OUTPUT_FILE}.partial")
        if partial_file.exists():
            partial_file.unlink()
        
        print("=" * 70 + "\n")
    
    else:
        print("\n❌ No embeddings generated!")
    
    client.close()

if __name__ == "__main__":
    import sys
    
    # Command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--full":
            print("\n🚀 Full mode - Building for ALL products\n")
            build_embeddings(limit=None, resume=False)
        
        elif sys.argv[1] == "--resume":
            print("\n🔄 Resume mode - Continuing from checkpoint\n")
            build_embeddings(limit=None, resume=True)
        
        elif sys.argv[1] == "--test":
            print("\n🧪 Test mode - First 100 products\n")
            build_embeddings(limit=100, resume=False)
        
        else:
            print(f"Unknown argument: {sys.argv[1]}")
            print("\nUsage:")
            print("  python build_embeddings.py          # Interactive mode")
            print("  python build_embeddings.py --test   # Test mode (100 products)")
            print("  python build_embeddings.py --full   # Full mode (all products)")
            print("  python build_embeddings.py --resume # Resume from checkpoint")
    
    else:
        # Interactive mode
        print("\n" + "=" * 70)
        print("  VASTR Embedding Builder - Interactive Mode")
        print("=" * 70)
        
        print("\nOptions:")
        print("1. Test mode (first 100 products) - Quick test (~5 minutes)")
        print("2. Sample mode (1000 products) - Medium test (~30 minutes)")
        print("3. Full mode (all products) - Complete build (2-4 hours)")
        print("4. Resume previous build")
        print()
        
        choice = input("Enter choice (1-4, default=1): ").strip()
        
        if choice == "2":
            print("\n✅ Sample mode selected (1000 products)")
            build_embeddings(limit=1000, resume=False)
        
        elif choice == "3":
            print("\n⚠️  Full mode - Building for ALL products!")
            print("   This will take 2-4 hours depending on your collection size.")
            confirm = input("   Continue? (yes/no): ").strip().lower()
            
            if confirm == "yes":
                build_embeddings(limit=None, resume=False)
            else:
                print("   Cancelled.")
        
        elif choice == "4":
            print("\n🔄 Resume mode - Continuing from checkpoint")
            build_embeddings(limit=None, resume=True)
        
        else:
            print("\n✅ Test mode selected (100 products)")
            build_embeddings(limit=100, resume=False)