import pandas as pd
import os
import shutil

# ========================= CONFIG =========================
INPUT_FILE     = "products_analysis.csv"
OUTPUT_DIR     = "final_400kb_csv_only"   # Plain CSV files here
MAX_TOTAL_KB   = 390                       # Total of ALL files < 400 KB
# =========================================================

# 1. Fresh start
if os.path.exists(OUTPUT_DIR):
    shutil.rmtree(OUTPUT_DIR)
os.makedirs(OUTPUT_DIR, exist_ok=True)

print("Loading data...")
df = pd.read_csv(INPUT_FILE)

# Remove brand column to save space (optional but helps a lot)
df = df.drop(columns=['brand_name'], errors='ignore')

print(f"Total rows: {len(df):,}\nSplitting into plain CSV files (total < 400 KB)...\n")

current_total_kb = 0
part_num = 1
start = 0

while start < len(df) and current_total_kb < MAX_TOTAL_KB:
    # Binary search for largest chunk that keeps total under limit
    low, high = start, len(df)
    best_end = start

    while low <= high:
        mid = (low + high) // 2
        chunk = df.iloc[start:mid]

        temp_file = os.path.join(OUTPUT_DIR, "temp.csv")
        chunk.to_csv(temp_file, index=False)
        size_kb = os.path.getsize(temp_file) / 1024
        os.remove(temp_file)

        if current_total_kb + size_kb <= MAX_TOTAL_KB:
            best_end = mid
            low = mid + 1
        else:
            high = mid - 1

    # If no progress, take at least 10 rows
    if best_end == start:
        best_end = min(start + 10, len(df))

    # Save final chunk
    final_chunk = df.iloc[start:best_end]
    output_file = os.path.join(OUTPUT_DIR, f"part_{part_num}.csv")
    final_chunk.to_csv(output_file, index=False)

    file_size_kb = os.path.getsize(output_file) / 1024
    current_total_kb += file_size_kb

    print(f"{os.path.basename(output_file)} → {len(final_chunk):,} rows → {file_size_kb:.1f} KB "
          f"(Total: {current_total_kb:.1f} KB)")

    start = best_end
    part_num += 1

print("\n" + "="*60)
print(f"DONE! Created {part_num-1} plain CSV file(s)")
print(f"Total size (all files): {current_total_kb:.1f} KB < 400 KB")
print(f"Folder: {OUTPUT_DIR}")
print("You can now zip or upload the entire folder safely!")
print("="*60)