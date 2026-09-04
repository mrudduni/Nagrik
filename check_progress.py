"""
check_progress.py
-----------------
Quickly checks the extraction progress and counts schemes in the cache.

Usage:
    python check_progress.py
"""

import json
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CACHE_FILE = pathlib.Path("ingestion/data/extracted.jsonl")
CLEANED_CSV = pathlib.Path("ingestion/data/cleaned.csv")

TOTAL_SCHEMES = 3397

if not CACHE_FILE.exists():
    print(f"Extraction not started yet. (0 / {TOTAL_SCHEMES} schemes, 0.0%)")
    sys.exit(0)

count = 0
valid_json = 0
ministries = set()

with open(CACHE_FILE, encoding="utf-8", errors="replace") as f:
    for line in f:
        line = line.strip()
        if line:
            count += 1
            try:
                data = json.loads(line)
                valid_json += 1
                if data.get("ministry"):
                    ministries.add(data["ministry"])
            except Exception:
                pass

pct = (count / TOTAL_SCHEMES) * 100
print("=" * 60)
print(f"  Extraction Progress : {count} / {TOTAL_SCHEMES} schemes ({pct:.1f}%)")
print(f"  Valid JSON Records  : {valid_json}")
print(f"  Unique Ministries   : {len(ministries)}")
print(f"  Remaining Schemes   : {max(0, TOTAL_SCHEMES - count)}")
print("=" * 60)
