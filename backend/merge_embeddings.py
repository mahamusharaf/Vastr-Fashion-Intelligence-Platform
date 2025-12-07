"""
Merge multiple NPZ embedding files into one
Removes duplicates and combines all unique embeddings
"""

import numpy as np
from datetime import datetime
import shutil
from pathlib import Path

# Files to merge
FILE_1 = "image_search_data.npz"  # 4,828 embeddings
FILE_2 = "image_search_data_first1326.npz"  # 1,313 embeddings
OUTPUT_FILE = "image_search_data_mergeduse.npz"

def merge_npz_files():
    print("=" * 80)
    print("  MERGE NPZ EMBEDDING FILES")
    print("=" * 80)
    
    # Load first file
    print(f"\n📂 Loading File 1: {FILE_1}")
    try:
        data1 = np.load(FILE_1, allow_pickle=True)
        embeddings1 = data1["embeddings"]
        product_ids1 = data1["product_ids"].tolist()
        
        print(f"   ✅ Loaded: {len(product_ids1):,} embeddings")
        print(f"   Shape: {embeddings1.shape}")
    except Exception as e:
        print(f"   ❌ Error loading {FILE_1}: {e}")
        return
    
    # Load second file
    print(f"\n📂 Loading File 2: {FILE_2}")
    try:
        data2 = np.load(FILE_2, allow_pickle=True)
        embeddings2 = data2["embeddings"]
        product_ids2 = data2["product_ids"].tolist()
        
        print(f"   ✅ Loaded: {len(product_ids2):,} embeddings")
        print(f"   Shape: {embeddings2.shape}")
    except Exception as e:
        print(f"   ❌ Error loading {FILE_2}: {e}")
        return
    
    # Check for overlaps
    print("\n🔍 Checking for overlaps...")
    
    set1 = set(product_ids1)
    set2 = set(product_ids2)
    
    overlap = set1 & set2  # Products in both files
    only_in_1 = set1 - set2
    only_in_2 = set2 - set1
    
    print(f"\n📊 Analysis:")
    print(f"   File 1 only: {len(only_in_1):,} products")
    print(f"   File 2 only: {len(only_in_2):,} products")
    print(f"   In both files: {len(overlap):,} products (duplicates)")
    print(f"   Total unique: {len(set1 | set2):,} products")
    
    if len(overlap) > 0:
        print(f"\n   ⚠️  {len(overlap):,} products exist in both files!")
        print(f"   Strategy: Keep from File 1 (larger file)")
    
    # Merge strategy: Keep all from File 1, add only unique from File 2
    print("\n🔨 Merging files...")
    
    # Start with all from File 1
    merged_product_ids = product_ids1.copy()
    merged_embeddings = embeddings1.copy()
    
    # Add only unique products from File 2
    added_count = 0
    for i, pid in enumerate(product_ids2):
        if pid not in set1:
            merged_product_ids.append(pid)
            merged_embeddings = np.vstack([merged_embeddings, embeddings2[i:i+1]])
            added_count += 1
    
    print(f"   ✅ Added {added_count:,} new products from File 2")
    print(f"   ✅ Skipped {len(overlap):,} duplicates")
    
    # Verify
    print(f"\n📊 Merged File Stats:")
    print(f"   Total embeddings: {len(merged_product_ids):,}")
    print(f"   Embedding shape: {merged_embeddings.shape}")
    print(f"   Unique product IDs: {len(set(merged_product_ids)):,}")
    
    # Check for any duplicates in merged file
    if len(merged_product_ids) != len(set(merged_product_ids)):
        print(f"   ⚠️  WARNING: Merged file has duplicates!")
        print(f"   Cleaning duplicates...")
        
        seen = set()
        clean_indices = []
        
        for i, pid in enumerate(merged_product_ids):
            if pid not in seen:
                seen.add(pid)
                clean_indices.append(i)
        
        merged_product_ids = [merged_product_ids[i] for i in clean_indices]
        merged_embeddings = merged_embeddings[clean_indices]
        
        print(f"   ✅ Cleaned: {len(merged_product_ids):,} unique products")
    
    # Save merged file
    print(f"\n💾 Saving merged file: {OUTPUT_FILE}")
    
    try:
        np.savez(
            OUTPUT_FILE,
            embeddings=merged_embeddings,
            product_ids=np.array(merged_product_ids),
            created_at=datetime.now().isoformat(),
            version='3.0_merged',
            source_files=[FILE_1, FILE_2]
        )
        
        # Get file size
        file_size = Path(OUTPUT_FILE).stat().st_size / (1024 * 1024)  # MB
        
        print(f"   ✅ Saved successfully!")
        print(f"   File size: {file_size:.1f} MB")
    except Exception as e:
        print(f"   ❌ Error saving: {e}")
        return
    
    # Show summary
    print("\n" + "=" * 80)
    print("  MERGE SUMMARY")
    print("=" * 80)
    
    print(f"\n   Before:")
    print(f"      {FILE_1}: {len(product_ids1):,} embeddings")
    print(f"      {FILE_2}: {len(product_ids2):,} embeddings")
    print(f"      Overlap: {len(overlap):,} duplicates")
    
    print(f"\n   After:")
    print(f"      {OUTPUT_FILE}: {len(merged_product_ids):,} embeddings")
    print(f"      Gain: +{added_count:,} new products")
    
    # Backup and replace
    print("\n" + "=" * 80)
    print("  NEXT STEPS")
    print("=" * 80)
    
    print(f"\n   The merged file has been created: {OUTPUT_FILE}")
    print(f"\n   Would you like to:")
    print(f"   1. Keep it as '{OUTPUT_FILE}' (manual rename later)")
    print(f"   2. Replace '{FILE_1}' with merged file (auto-backup original)")
    print(f"   3. Do nothing (just keep the merged file)")
    
    choice = input(f"\n   Enter choice (1-3): ").strip()
    
    if choice == "2":
        # Backup original
        backup_file = f"{FILE_1}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy(FILE_1, backup_file)
        print(f"\n   ✅ Backed up {FILE_1} to {backup_file}")
        
        # Replace with merged
        shutil.copy(OUTPUT_FILE, FILE_1)
        print(f"   ✅ Replaced {FILE_1} with merged file")
        print(f"\n   🎉 Done! Restart your API server to use the merged embeddings.")
        print(f"   Your API will now have {len(merged_product_ids):,} products!")
    
    elif choice == "1":
        print(f"\n   ✅ Merged file saved as: {OUTPUT_FILE}")
        print(f"   To use it, either:")
        print(f"      - Rename it to '{FILE_1}'")
        print(f"      - Update image_search.py to load '{OUTPUT_FILE}'")
    
    else:
        print(f"\n   ✅ Merged file saved as: {OUTPUT_FILE}")
        print(f"   No changes made to existing files.")
    
    print("\n" + "=" * 80)
    print("  VERIFICATION")
    print("=" * 80)
    
    print(f"\n   You can verify the merged file with:")
    print(f"   python check_npz_duplicates.py")
    print(f"   (Update EMBEDDINGS_FILE to '{OUTPUT_FILE}' in the script)")
    
    print("=" * 80 + "\n")

def list_npz_files():
    """List all NPZ files in current directory"""
    
    print("\n📁 NPZ files in current directory:")
    
    from pathlib import Path
    npz_files = list(Path(".").glob("*.npz"))
    
    if not npz_files:
        print("   No NPZ files found!")
        return []
    
    file_info = []
    
    for npz_file in npz_files:
        try:
            data = np.load(str(npz_file), allow_pickle=True)
            count = len(data["product_ids"])
            size_mb = npz_file.stat().st_size / (1024 * 1024)
            
            file_info.append({
                'name': npz_file.name,
                'count': count,
                'size': size_mb
            })
            
            print(f"\n   {npz_file.name}")
            print(f"      Products: {count:,}")
            print(f"      Size: {size_mb:.1f} MB")
        except Exception as e:
            print(f"\n   {npz_file.name}")
            print(f"      Error reading: {e}")
    
    return file_info

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--list":
        list_npz_files()
    
    else:
        print("\nThis script will merge two NPZ embedding files.")
        print(f"File 1: {FILE_1}")
        print(f"File 2: {FILE_2}")
        
        # First, list available files
        available_files = list_npz_files()
        
        # Check if files exist
        if not Path(FILE_1).exists():
            print(f"\n❌ Error: {FILE_1} not found!")
            print(f"Update FILE_1 in the script to the correct filename.")
            exit(1)
        
        if not Path(FILE_2).exists():
            print(f"\n❌ Error: {FILE_2} not found!")
            print(f"Update FILE_2 in the script to the correct filename.")
            exit(1)
        
        print(f"\n{'=' * 80}")
        confirm = input("Proceed with merge? (yes/no): ").strip().lower()
        
        if confirm == "yes":
            merge_npz_files()
        else:
            print("\nCancelled.")