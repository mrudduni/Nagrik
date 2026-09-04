import pathlib, json

checks = []
checks.append(("updated_data.csv exists", pathlib.Path("updated_data.csv").exists()))
checks.append(("cleaned.csv exists", pathlib.Path("ingestion/data/cleaned.csv").exists()))

extracted = pathlib.Path("ingestion/data/extracted.jsonl")
if extracted.exists():
    lines = [l for l in open(extracted, encoding="utf-8") if l.strip()]
    checks.append((f"extracted.jsonl ({len(lines)} records)", True))
else:
    checks.append(("extracted.jsonl", False))

src_files = [
    "ingestion/clean.py", "ingestion/extract.py", "ingestion/load_graph.py",
    "ingestion/embed.py", "api/main.py", "api/graph.py", "api/models.py",
    "api/eligibility.py", "test_search.py", "requirements.txt", "README.md",
    ".env.example", "create_mock_extraction.py", "setup_check.py",
]
all_src_ok = all(pathlib.Path(f).exists() for f in src_files)
checks.append((f"All {len(src_files)} source files present", all_src_ok))

for label, ok in checks:
    status = "PASS" if ok else "FAIL"
    print(f"  {status}  {label}")

if extracted.exists():
    recs = [json.loads(l) for l in open(extracted, encoding="utf-8") if l.strip()]
    print()
    print("Mock extraction sample:")
    for r in recs[:3]:
        print(f"  {r['_scheme_id']}: {len(r.get('eligibility_rules',[]))} rules, states={r.get('applicable_states',[])[0]}")
