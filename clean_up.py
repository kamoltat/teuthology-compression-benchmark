import os
from glob import glob

# Delete results files
results_files = glob("results_*.csv") + glob("results_*.json")
for file in results_files:
    os.remove(file)
    print(f"Deleted: {file}")

print(f"Cleaned up {len(results_files)} files")
