# Nagrik 🇮🇳

> **Schema-driven, voice-first government form filling platform for Indian citizens.**

Nagrik lets a citizen complete government forms (Aadhaar, PAN, Voter ID, …) through a natural voice conversation — on the web or via a phone call — without ever needing to read a form.

---

## Repository Structure

```
Nagrik/
├── backend/                  # Voice-agent FastAPI server (main application)
│   ├── agents/               # Gemini function-calling agent
│   ├── api/routes/           # FastAPI routers (sessions, twilio)
│   ├── core/                 # Config (pydantic-settings)
│   ├── db/                   # SQLAlchemy models & DB engine
│   └── services/             # Schema parser · State manager · Validation
│
├── frontend/                 # Next.js citizen & government portal
│
├── schemes_api/              # Knowledge-graph API (Neo4j + Supabase)
│   ├── main.py               # FastAPI app: scheme search & recommendations
│   ├── graph.py              # Neo4j vector search + traversal
│   ├── eligibility.py        # Deterministic eligibility evaluation
│   ├── auth.py               # Supabase JWT auth
│   └── models.py             # Pydantic models
│
├── ingestion/                # Data pipeline: extract → clean → embed → load
│
├── schemas/                  # Government form JSON schemas (source of truth)
│   ├── aadhaar_enrolment_form1.json
│   ├── pan_card_49a.json
│   ├── voter_id_form6.json
│   └── public_grievance.json
│
├── scripts/                  # One-off utility & verification scripts
├── docs/                     # Output artefacts, sample outputs
├── templates/                # Legacy HTML voice UI (index.html)
│
├── main.py                   # Voice-agent server entrypoint
└── requirements.txt          # Python dependencies
```

---

## Quick Start — Voice Agent

```bash
# 1. Create and activate virtualenv
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Mac/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set environment variables
cp .env.example .env            # then fill in your keys

# 4. Run the server
python main.py
# → http://localhost:8000
```

### Required environment variables

| Variable | Purpose |
|---|---|
| `GEMINI_API_KEY` | Google Gemini API key (LLM + function calling) |
| `TWILIO_ACCOUNT_SID` | Twilio account SID (phone calls) |
| `TWILIO_AUTH_TOKEN` | Twilio auth token |
| `TWILIO_PHONE_NUMBER` | Your Twilio phone number |

---

## Quick Start — Schemes API

```bash
cd schemes_api
# Install additional deps: sentence-transformers, neo4j, supabase
uvicorn schemes_api.main:app --reload
# → http://localhost:8000/docs
```

---

## Key APIs (Voice Agent)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/forms` | List all available form schemas |
| `GET` | `/api/forms/{id}/schema` | Get raw JSON schema |
| `POST` | `/api/sessions` | Create a new form session |
| `GET` | `/api/sessions/{id}` | Get session state |
| `POST` | `/api/chat` | Send a message, get agent response |
| `POST` | `/api/twilio/voice` | Twilio inbound call webhook |
| `POST` | `/api/twilio/gather` | Twilio speech gather webhook |

---

## Architecture

```
User (Web / Phone)
        │
   FastAPI (main.py)
        │
   FormAgent (Gemini + function calling)
        ├── update_form_field()  ──→  StateManager  ──→  ValidationService
        └── confirm_field()      ──→  SchemaParser   ──→  DB (SQLite/Postgres)
```

- **LLM** handles: natural language understanding, extraction, Q&A, paraphrasing
- **Deterministic code** handles: schema rules, validation, state transitions, persistence

---

## Supported Forms

| Form | Schema File |
|---|---|
| Aadhaar Enrolment / Update (Form 1) | `schemas/aadhaar_enrolment_form1.json` |
| PAN Card Application (Form 49A) | `schemas/pan_card_49a.json` |
| Voter Registration (Form 6) | `schemas/voter_id_form6.json` |
| Public Grievance | `schemas/public_grievance.json` |

New forms can be added by dropping a JSON schema into `schemas/` — no code changes required.

---

## License

[GPL-3.0](LICENSE)
