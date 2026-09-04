"""
test_search.py
--------------
Sanity-check script: runs 5 sample citizen profiles against POST /schemes/search
and prints structured results.

Usage:
    python test_search.py [--base-url http://localhost:8000]
"""

import argparse
import sys
import requests

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DEFAULT_BASE_URL = "http://localhost:8000"

PROFILES = [
    {
        "label": "SC farmer in Rajasthan, low income",
        "payload": {
            "state": "Rajasthan",
            "occupation": "farmer",
            "income_annual": 80000,
            "category": "SC",
            "age": 42,
            "gender": "male",
            "disability": False,
            "marital_status": "married",
            "query": "I am a small farmer looking for financial assistance or crop subsidies",
        },
    },
    {
        "label": "Young woman entrepreneur, OBC, Maharashtra",
        "payload": {
            "state": "Maharashtra",
            "occupation": "entrepreneur",
            "income_annual": 250000,
            "category": "OBC",
            "age": 27,
            "gender": "female",
            "disability": False,
            "marital_status": "single",
            "query": "I want to start a small business and need a loan or grant",
        },
    },
    {
        "label": "ST student in tribal area, Odisha",
        "payload": {
            "state": "Odisha",
            "occupation": "student",
            "income_annual": 40000,
            "category": "ST",
            "age": 19,
            "gender": "male",
            "disability": False,
            "marital_status": "single",
            "query": "Looking for scholarships or educational support for tribal students",
        },
    },
    {
        "label": "Disabled widowed woman, Delhi, general category",
        "payload": {
            "state": "Delhi",
            "occupation": "unemployed",
            "income_annual": 30000,
            "category": "General",
            "age": 55,
            "gender": "female",
            "disability": True,
            "marital_status": "widowed",
            "query": "Need pension or social welfare support as a disabled widow",
        },
    },
    {
        "label": "Construction worker, UP, seeking health insurance",
        "payload": {
            "state": "Uttar Pradesh",
            "occupation": "labourer",
            "income_annual": 120000,
            "category": "OBC",
            "age": 35,
            "gender": "male",
            "disability": False,
            "marital_status": "married",
            "query": "Construction worker looking for health insurance or medical benefit scheme",
        },
    },
]


def format_rule(e):
    return f"{e['field']} {e['operator']} {e['value']}"


def print_result(profile_label: str, data: dict):
    print(f"\n{'=' * 70}")
    print(f"PROFILE: {profile_label}")
    print(f"QUERY:   {data.get('query', '')}")
    print(f"TOTAL CANDIDATES: {data.get('total_candidates', 0)}")
    print()

    results = data.get("results", [])[:5]  # Show top 5
    for i, r in enumerate(results, 1):
        status_icon = {"Eligible": "PASS", "Uncertain": "UNK", "Not Eligible": "FAIL"}.get(
            r["eligibility_status"], "?"
        )
        print(f"  {i}. [{status_icon} | {r['eligibility_status']:12s}] {r['scheme_name'][:60]}")
        print(f"     Vector Score: {r.get('vector_score', 0):.4f}")
        print(f"     Summary: {r.get('summary', '')[:120]}")
        if r.get("source_url"):
            print(f"     URL: {r['source_url']}")

        failed = [e for e in r.get("rule_evaluations", []) if e["status"] == "failed"]
        passed = [e for e in r.get("rule_evaluations", []) if e["status"] == "passed"]
        if failed:
            failed_str = ", ".join(format_rule(e) for e in failed[:3])
            print(f"     Failed rules: {failed_str}")
        if passed:
            passed_str = ", ".join(format_rule(e) for e in passed[:3])
            print(f"     Passed rules: {passed_str}")
        print()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    args = parser.parse_args()

    base = args.base_url.rstrip("/")
    endpoint = f"{base}/schemes/search"

    print(f"Testing API at: {endpoint}")
    print(f"Running {len(PROFILES)} citizen profiles ...\n")

    all_ok = True
    for profile in PROFILES:
        try:
            resp = requests.post(endpoint, json=profile["payload"], timeout=30)
            if resp.status_code == 200:
                print_result(profile["label"], resp.json())
            else:
                print(f"\n[ERROR] {profile['label']}: HTTP {resp.status_code}")
                print(f"  {resp.text[:300]}")
                all_ok = False
        except requests.exceptions.ConnectionError:
            print(f"\n[ERROR] Cannot connect to {endpoint}")
            print("  Make sure the API server is running: python -m uvicorn api.main:app --reload")
            sys.exit(1)
        except Exception as e:
            print(f"\n[ERROR] {profile['label']}: {e}")
            all_ok = False

    print("\n" + "=" * 70)
    print(f"Test complete. Status: {'All passed' if all_ok else 'Some profiles had errors'}")


if __name__ == "__main__":
    main()
