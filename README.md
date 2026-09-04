# Nagrik

An AI-powered Digital Citizen Companion that acts as an intelligent interface between citizens and government.

## Government Schemes Knowledge Graph Backend

A FastAPI + Neo4j (5.x native vector index) backend for retrieving and recommending Indian government welfare schemes.

**Dataset**: `updated_data.csv` — 3,400 schemes with eligibility text, benefits, documents, categories, and application steps.

---

## Architecture

```
updated_data.csv
     │
     ▼
ingestion/clean.py        → ingestion/data/cleaned.csv
     │
     ▼
ingestion/extract.py      → ingestion/data/extracted.jsonl
  (Gemini 2.5 Flash LLM extraction with caching)
     │
     ▼
ingestion/load_graph.py   → Neo4j Knowledge Graph
  (:Ministry)-[:HAS_DEPARTMENT]->(:Department)
    -[:OFFERS]->(:Scheme)
      -[:HAS_RULE]->(:EligibilityRule)
      -[:REQUIRES]->(:Document)
      -[:APPLICABLE_IN]->(:State)
      -[:FOR_CATEGORY]->(:BeneficiaryCategory)
     │
     ▼
ingestion/embed.py        → Scheme.embedding (384-dim, cosine)
  Vector index: scheme_embeddings
     │
     ▼
api/main.py               → FastAPI (port 8000)
  POST /schemes/search
  GET  /schemes/{id}/similar
```

---

## Prerequisites

| Requirement | Notes |
|---|---|
| Python 3.11+ | |
| Neo4j 5.x | Community or Enterprise; must have vector index support |
| Gemini API key | Free at [aistudio.google.com](https://aistudio.google.com/app/apikey) |

---

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment

```bash
copy .env.example .env
# Edit .env with your Neo4j credentials and Gemini API key
```

Get a free Gemini API key at: https://aistudio.google.com/app/apikey

### 3. Start Neo4j

Make sure Neo4j 5.x is running. Quick option with Docker:

```bash
docker run -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/your_password \
  neo4j:5
```

### 4. Run pre-flight check

```bash
python setup_check.py
```

This verifies Python version, packages, .env keys, Neo4j connectivity, and data files before you start.

---

## Run Order

### Step 1 — Clean the dataset

```bash
python ingestion/clean.py
```

- Reads `updated_data.csv`
- Drops duplicates and rows missing scheme name / eligibility text
- Normalizes categories and generates `source_url` from slugs
- Outputs `ingestion/data/cleaned.csv`

### Step 2 — LLM extraction (Gemini 2.5 Flash)

```bash
# Test with 10 rows first:
python ingestion/extract.py --limit 10

# Full run (~3,397 calls, uses incremental cache):
python ingestion/extract.py
```




```bash
python create_mock_extraction.py
# Creates ingestion/data/extracted.jsonl with 10 representative schemes
# covering SC/ST/OBC, farmers, widows, disabled persons, construction workers
```

### Step 3 — Build Neo4j graph

```bash
python ingestion/load_graph.py
```

- Reads `extracted.jsonl`
- Uses `MERGE` throughout — fully idempotent (safe to re-run)
- Prints node counts on completion

### Step 4 — Generate embeddings

```bash
python ingestion/embed.py
```

- Downloads `all-MiniLM-L6-v2` (22 MB, first run only)
- Embeds each scheme's summary (384-dim, cosine)
- Creates vector index `scheme_embeddings` in Neo4j

### Step 5 — Start the API server

```bash
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

Interactive docs: [http://localhost:8000/docs](http://localhost:8000/docs)

### Step 6 — Run sanity-check tests

```bash
python test_search.py
```

Runs 5 citizen profiles and prints top-5 results per profile with eligibility status.

---

## API Reference

### `POST /schemes/search`

Search for schemes matching a citizen's profile and free-text need.

**Request body:**

```json
{
  "state": "Rajasthan",
  "occupation": "farmer",
  "income_annual": 80000,
  "category": "SC",
  "age": 42,
  "gender": "male",
  "disability": false,
  "marital_status": "married",
  "query": "I am a small farmer looking for financial assistance or crop subsidies"
}
```

**Response:**

```json
{
  "query": "...",
  "total_candidates": 12,
  "results": [
    {
      "scheme_id": "pm-kisan",
      "scheme_name": "PM-KISAN",
      "summary": "...",
      "source_url": "https://www.myscheme.gov.in/schemes/pm-kisan",
      "last_verified": "2026-08-26T09:00:00+00:00",
      "eligibility_status": "Eligible",
      "rule_evaluations": [
        {"field": "occupation", "operator": "eq", "value": "farmer", "status": "passed"}
      ],
      "vector_score": 0.8923
    }
  ]
}
```

**Eligibility statuses:**

| Status | Meaning |
|---|---|
| `Eligible` | All rules passed against citizen profile |
| `Not Eligible` | At least one rule failed |
| `Uncertain` | Some rules couldn't be evaluated (missing profile data) |

---

## `GET /schemes/{id}/similar`

Get up to 5 similar schemes via shared-neighbor graph traversal.

**Response:**

```json
{
  "scheme_id": "pm-kisan",
  "similar_schemes": [
    {
      "scheme_id": "kcc-scheme",
      "scheme_name": "Kisan Credit Card Scheme",
      "summary": "...",
      "overlap_count": 4,
      "shared_via": ["BeneficiaryCategory", "State", "EligibilityRule"],
      "reason": "Also targets similar beneficiary groups; applicable in the same state(s)"
    }
  ]
}
```

---

## Project Structure

```
├── updated_data.csv              # Raw dataset
├── .env.example                  # Environment variable template
├── requirements.txt
├── README.md
├── test_search.py                # Sanity-check test script
│
├── ingestion/
│   ├── clean.py                  # Step 1: Clean & normalize
│   ├── extract.py                # Step 2: Gemini LLM extraction
│   ├── load_graph.py             # Step 3: Build Neo4j graph
│   ├── embed.py                  # Step 4: Embeddings + vector index
│   └── data/
│       ├── cleaned.csv           # Output of clean.py
│       └── extracted.jsonl       # Output of extract.py (cached)
│
└── api/
    ├── main.py                   # FastAPI app
    ├── graph.py                  # Neo4j driver + Cypher helpers
    ├── models.py                 # Pydantic request/response models
    └── eligibility.py            # Deterministic rule evaluator
```

---

## Notes

- **Re-running extraction**: `extract.py` appends to `extracted.jsonl` and skips already-processed schemes. Delete the file to start fresh.
- **Rate limits**: Gemini free tier allows ~15 RPM. The script uses 0.3s delays + exponential backoff on 429 errors.
- **Vector dimensions**: Using `all-MiniLM-L6-v2` (384-dim). If you switch models, delete the index in Neo4j and re-run `embed.py`.
