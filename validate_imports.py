"""
validate_imports.py
-------------------
Quick check that all required packages are installed.
"""
import sys

packages = [
    ("pandas", "pandas"),
    ("neo4j", "neo4j"),
    ("google.generativeai", "google-generativeai"),
    ("sentence_transformers", "sentence-transformers"),
    ("fastapi", "fastapi"),
    ("uvicorn", "uvicorn"),
    ("pydantic", "pydantic"),
    ("dotenv", "python-dotenv"),
    ("requests", "requests"),
]

all_ok = True
for module, pkg_name in packages:
    try:
        __import__(module)
        print(f"  OK  {pkg_name}")
    except ImportError:
        print(f"  MISSING  {pkg_name}  (install: pip install {pkg_name})")
        all_ok = False

if all_ok:
    print("\nAll packages installed correctly!")
else:
    print("\nSome packages are missing. Run: pip install -r requirements.txt")
    sys.exit(1)
