"""
setup_check.py
--------------
Pre-flight check: verifies all dependencies, connectivity, and configuration
are ready before running the ingestion pipeline.

Usage:
    python setup_check.py
"""
import sys
import os
import pathlib
import socket

print("=" * 60)
print("Government Schemes KG — Pre-flight Check")
print("=" * 60)

PASS = "[PASS]"
FAIL = "[FAIL]"
WARN = "[WARN]"

all_ok = True


def check(label, condition, fail_msg="", warn=False):
    global all_ok
    status = PASS if condition else (WARN if warn else FAIL)
    if not condition and not warn:
        all_ok = False
    print(f"  {status}  {label}")
    if not condition and fail_msg:
        print(f"         -> {fail_msg}")
    return condition


print("\n[1] Python version")
check(
    f"Python {sys.version_info.major}.{sys.version_info.minor}",
    sys.version_info >= (3, 11),
    "Requires Python 3.11+. Install from https://python.org",
)

print("\n[2] Required packages")
for module, pkg in [
    ("pandas", "pandas"),
    ("neo4j", "neo4j"),
    ("google.genai", "google-genai"),
    ("sentence_transformers", "sentence-transformers"),
    ("fastapi", "fastapi"),
    ("uvicorn", "uvicorn"),
    ("pydantic", "pydantic"),
    ("dotenv", "python-dotenv"),
    ("requests", "requests"),
]:
    try:
        __import__(module)
        check(pkg, True)
    except ImportError:
        check(pkg, False, f"pip install {pkg}")

print("\n[3] .env / credentials")
env_path = pathlib.Path(".env")
check(".env file exists", env_path.exists(),
      "Copy .env.example to .env and fill in your credentials:\n"
      "         copy .env.example .env")

if env_path.exists():
    from dotenv import load_dotenv
    load_dotenv()

neo4j_uri = os.getenv("NEO4J_URI", "")
neo4j_pass = os.getenv("NEO4J_PASSWORD", "")
llm_key = os.getenv("LLM_API_KEY") or os.getenv("GEMINI_API_KEY") or ""

check("NEO4J_URI set", bool(neo4j_uri),
      "Set NEO4J_URI in .env (e.g. bolt://localhost:7687)")
check("NEO4J_PASSWORD set", bool(neo4j_pass),
      "Set NEO4J_PASSWORD in .env")
check("LLM_API_KEY set", bool(llm_key),
      "Set LLM_API_KEY in .env\n"
      "         Get free Gemini key: https://aistudio.google.com/app/apikey")

print("\n[4] Neo4j connectivity")
neo4j_host = "localhost"
neo4j_bolt_port = 7687
if neo4j_uri:
    try:
        uri_parts = neo4j_uri.replace("bolt://", "").replace("neo4j://", "").split(":")
        neo4j_host = uri_parts[0]
        neo4j_bolt_port = int(uri_parts[1]) if len(uri_parts) > 1 else 7687
    except Exception:
        pass

try:
    s = socket.create_connection((neo4j_host, neo4j_bolt_port), timeout=3)
    s.close()
    check(f"Neo4j reachable at {neo4j_host}:{neo4j_bolt_port}", True)
except (ConnectionRefusedError, OSError):
    check(f"Neo4j reachable at {neo4j_host}:{neo4j_bolt_port}", False,
          "Start Neo4j Desktop or run: docker run -p 7474:7474 -p 7687:7687 "
          "-e NEO4J_AUTH=neo4j/your_password neo4j:5")

print("\n[5] Data files")
check("updated_data.csv exists", pathlib.Path("updated_data.csv").exists(),
      "Place updated_data.csv in the project root")
check("ingestion/data/cleaned.csv exists",
      pathlib.Path("ingestion/data/cleaned.csv").exists(),
      "Run: python ingestion/clean.py")

extracted = pathlib.Path("ingestion/data/extracted.jsonl")
if extracted.exists():
    lines = sum(1 for _ in open(extracted, encoding="utf-8") if _.strip())
    check(f"extracted.jsonl exists ({lines} records)", True)
else:
    check("extracted.jsonl exists", False, warn=True,
          fail_msg="Run: python ingestion/extract.py (or python create_mock_extraction.py for testing)")

print("\n" + "=" * 60)
if all_ok:
    print("All checks passed! Ready to run the pipeline.")
    print("\nNext step:")
    if not extracted.exists():
        print("  python ingestion/extract.py   # or python create_mock_extraction.py")
    else:
        print("  python ingestion/load_graph.py")
else:
    print("Some checks failed. Fix the issues above, then re-run.")
    print("See README.md for detailed setup instructions.")
print("=" * 60)
