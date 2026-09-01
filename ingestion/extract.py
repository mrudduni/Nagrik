"""
ingestion/extract.py
--------------------
Step 2: Resilient Multi-Key Parallel Gemini Scheme Extractor.
Pools all Gemini API keys with automatic rate-limit (429) backoff,
respecting Google's retryDelay cooldowns so no scheme fails.

Usage:
    python ingestion/extract.py [--concurrency 3] [--limit N]

Output:
    ingestion/data/extracted.jsonl
"""

import argparse
import concurrent.futures
import json
import os
import pathlib
import re
import sys
import textwrap
import threading
import time
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
from dotenv import load_dotenv

load_dotenv()

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT = pathlib.Path(__file__).parent.parent
CLEANED_CSV = pathlib.Path(__file__).parent / "data" / "cleaned.csv"
CACHE_FILE = pathlib.Path(__file__).parent / "data" / "extracted.jsonl"

# ── Gemini Multi-Key Pool Setup ───────────────────────────────────────────────
import google.genai as genai
from google.genai import types as genai_types

raw_gemini_keys = os.getenv("GEMINI_KEYS", "") or os.getenv("LLM_API_KEY", "")
gemini_keys_list = [k.strip() for k in re.split(r"[,;\s]+", raw_gemini_keys) if k.strip()]


class GeminiKeyPool:
    """Manages a pool of Gemini API keys with intelligent backoff and pacing."""
    def __init__(self, keys: List[str]):
        self.providers = []
        for i, k in enumerate(keys):
            client = None
            try:
                client = genai.Client(api_key=k)
            except Exception as e:
                print(f"[warning] Failed to init client for key {i+1}: {e}")

            self.providers.append({
                "id": i + 1,
                "key": k,
                "name": f"Gemini-{i+1} (..{k[-6:]})",
                "client": client,
                "cooldown_until": 0.0,
                "disabled": False,
            })

        self.index = 0
        self.lock = threading.Lock()

    def get_client_entry(self) -> Dict[str, Any]:
        while True:
            wait_time = 0.0
            chosen = None
            with self.lock:
                now = time.time()
                active = [p for p in self.providers if not p["disabled"] and p["client"] is not None]
                if not active:
                    raise RuntimeError("All Gemini API keys are disabled.")

                for _ in range(len(active)):
                    p = active[self.index % len(active)]
                    self.index = (self.index + 1) % len(active)
                    if p["cooldown_until"] <= now:
                        # Add a small staggered offset for the next caller
                        p["cooldown_until"] = now + 1.2
                        chosen = p
                        break

                if chosen is None:
                    earliest = min(active, key=lambda x: x["cooldown_until"])
                    wait_time = max(0.2, earliest["cooldown_until"] - now)

            if chosen is not None:
                return chosen

            # Sleep OUTSIDE the lock so other threads aren't blocked
            time.sleep(min(wait_time + 0.5, 30.0))

    def report_result(self, entry: Dict[str, Any], is_success: bool, err_msg: str = ""):
        with self.lock:
            now = time.time()
            if is_success:
                # Small polite pacing (1.5s) to avoid bursting rate limit
                entry["cooldown_until"] = max(entry["cooldown_until"], now + 1.5)
            else:
                if "404" in err_msg or "INVALID_ARGUMENT" in err_msg:
                    entry["disabled"] = True
                    print(f"\n⚠️  Disabled {entry['name']}: {err_msg[:60]}")
                elif "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg:
                    # Distinguish daily quota exhaustion from per-minute rate limits
                    is_daily_quota = "FreeTier" in err_msg or "day" in err_msg.lower() or "daily" in err_msg.lower()
                    if is_daily_quota:
                        # Daily quota hit — disable this key for the session
                        entry["disabled"] = True
                        print(f"\n🚫 Daily quota exhausted on {entry['name']} — disabling for today.")
                    else:
                        # Per-minute rate limit — extract suggested retry delay
                        match = re.search(r"retry in (\d+(?:\.\d+)?)s", err_msg)
                        wait_sec = float(match.group(1)) if match else 25.0
                        entry["cooldown_until"] = now + wait_sec + 2.0
                        print(f"\n⏳ Rate limit on {entry['name']}, cooling down for {int(wait_sec)}s...")
                else:
                    entry["cooldown_until"] = now + 4.0


key_pool = GeminiKeyPool(gemini_keys_list)

# ── Prompt Template ───────────────────────────────────────────────────────────
SYSTEM_PROMPT = textwrap.dedent("""
You are a structured data extractor for Indian government welfare schemes.
Given raw text about a scheme, return ONLY a valid JSON object conforming exactly to this structure:
{
  "scheme_name": "<string>",
  "ministry": "<string or null>",
  "department": "<string or null>",
  "summary": "<concise 2-3 sentence summary of what the scheme offers>",
  "eligibility_rules": [
    {"field": "<field>", "operator": "<op>", "value": "<val>"}
  ],
  "required_documents": ["<doc1>", "<doc2>"],
  "beneficiary_categories": ["<cat1>", "<cat2>"],
  "applicable_states": ["<state1>"],
  "source_url": "<url or null>"
}

Operators MUST be one of: eq, ne, lt, lte, gt, gte, in, not_in, contains.
Fields should be snake_case (e.g. age, gender, income_annual, category, occupation, residence_state, disability, marital_status).
For pan-India schemes, set "applicable_states" to ["All India"].
Return ONLY the raw JSON object.
""").strip()


def build_prompt(row: dict) -> str:
    parts = [
        f"Scheme Name: {row.get('scheme_name', '')}",
        f"Level: {row.get('level', '')}",
        f"Category: {row.get('schemeCategory', '')}",
        f"Tags: {row.get('tags', '')}",
        f"Details: {str(row.get('details', ''))[:1200]}",
        f"Eligibility: {str(row.get('eligibility', ''))[:1000]}",
        f"Benefits: {str(row.get('benefits', ''))[:400]}",
        f"Documents: {str(row.get('documents', ''))[:400]}",
        f"Source URL: {row.get('source_url', '')}",
    ]
    return "\n".join(parts)


def clean_json_text(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.MULTILINE)
        text = re.sub(r"\s*```$", "", text, flags=re.MULTILINE)
    return text.strip()


def call_gemini_pool(prompt: str, retries: int = 8) -> Optional[Tuple[dict, str]]:
    """Calls Gemini with exponential retry backoff so rate limits never drop schemes."""
    for attempt in range(1, retries + 1):
        entry = key_pool.get_client_entry()
        client = entry["client"]
        try:
            res = client.models.generate_content(
                model="gemini-3.5-flash-lite",
                contents=[SYSTEM_PROMPT, prompt],
                config=genai_types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.0,
                    max_output_tokens=1200,
                ),
            )
            raw = clean_json_text(res.text)
            parsed = json.loads(raw)
            key_pool.report_result(entry, is_success=True)
            return parsed, entry["name"]
        except json.JSONDecodeError:
            pass
        except Exception as e:
            msg = str(e)
            key_pool.report_result(entry, is_success=False, err_msg=msg)
            time.sleep(2.0 * attempt)
    return None


def load_cached_ids() -> set[str]:
    done = set()
    if CACHE_FILE.exists():
        with open(CACHE_FILE, encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        obj = json.loads(line)
                        sid = obj.get("_scheme_id") or obj.get("scheme_id")
                        if sid:
                            done.add(sid)
                    except Exception:
                        pass
    return done


def main():
    import sys
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description="Multi-Key Parallel Gemini Scheme Extractor")
    parser.add_argument("--concurrency", type=int, default=3,
                        help="Number of concurrent worker threads (default: 3)")
    parser.add_argument("--limit", type=int, default=None,
                        help="Process at most N rows")
    args = parser.parse_args()

    if not CLEANED_CSV.exists():
        sys.exit(f"Cleaned dataset not found: {CLEANED_CSV}. Run ingestion/clean.py first.")

    df = pd.read_csv(CLEANED_CSV, encoding="utf-8")
    print(f"[extract] Loaded {len(df)} cleaned rows from {CLEANED_CSV}")

    already_done = load_cached_ids()
    print(f"[extract] Already cached: {len(already_done)} rows.")

    rows = df.to_dict(orient="records")
    if args.limit:
        rows = rows[: args.limit]

    pending = [r for r in rows if r["scheme_id"] not in already_done]
    total_to_process = len(pending)
    print(f"[extract] To process: {total_to_process} schemes using {len(key_pool.providers)} Gemini keys ({args.concurrency} parallel workers).")

    if total_to_process == 0:
        print("[extract] All schemes already extracted! Ready for load_graph.py.")
        return

    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    cache_lock = threading.Lock()
    progress_lock = threading.Lock()

    completed_count = 0
    success_count = 0
    failed_count = 0
    start_time = time.time()

    def process_row(row: dict):
        nonlocal completed_count, success_count, failed_count
        scheme_id = row["scheme_id"]
        prompt = build_prompt(row)

        res = call_gemini_pool(prompt)

        with progress_lock:
            completed_count += 1
            idx = completed_count
            elapsed = time.time() - start_time
            rate = idx / elapsed if elapsed > 0 else 0
            eta = (total_to_process - idx) / rate if rate > 0 else 0

        if res is not None:
            parsed, provider_name = res
            parsed["_scheme_id"] = scheme_id
            parsed["_slug"] = row.get("slug", "")
            parsed["source_url"] = parsed.get("source_url") or row.get("source_url", "")

            with cache_lock:
                with open(CACHE_FILE, "a", encoding="utf-8") as f:
                    f.write(json.dumps(parsed, ensure_ascii=False) + "\n")
                    f.flush()

            with progress_lock:
                success_count += 1
                curr_total = len(already_done) + success_count
                pct = (curr_total / len(df)) * 100
                print(f"[{curr_total}/{len(df)}] ({pct:.1f}%) {scheme_id[:32]} -> OK ({provider_name}) [{rate:.2f} req/s, ETA: {eta/60:.1f}m]")
        else:
            with progress_lock:
                failed_count += 1
                curr_total = len(already_done) + success_count
                pct = (curr_total / len(df)) * 100
                print(f"[{curr_total}/{len(df)}] ({pct:.1f}%) {scheme_id[:32]} -> FAILED [{rate:.2f} req/s]")

    print(f"\n[extract] Starting parallel extraction across {len(key_pool.providers)} Gemini keys...\n")
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrency) as executor:
        futures = [executor.submit(process_row, r) for r in pending]
        concurrent.futures.wait(futures)

    total_time = time.time() - start_time
    print(f"\n[extract] Extraction Complete in {total_time/60:.2f} minutes!")
    print(f"  Success: {success_count}")
    print(f"  Failed:  {failed_count}")
    print(f"  Total Cached in JSONL: {len(already_done) + success_count}")


if __name__ == "__main__":
    main()
