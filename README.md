# Nagrik 🇮🇳

> **AI-powered Digital Citizen Companion — scheme discovery, complaint filing, and application assistance for Indian citizens.**

Nagrik lets citizens discover government schemes, file civic complaints, and get application assistance through a natural text or voice conversation, in English, Hindi, Tamil, Marathi, and more.

---

## Quick Start — run everything with one command

**Prerequisites:** Python 3.10+, Node.js 18+

```powershell
# From the repo root:
.\start.ps1
```

Or double-click **`start.bat`**.

This opens separate terminal windows for the complete platform:

| Service | Port | Description |
|---------|------|-------------|
| Next.js Frontend | http://localhost:3000 | Citizen App + Government Analytics Dashboard |
| FastAPI AI Backend | http://127.0.0.1:8000 | Voice & Chatbot Agent, Sarvam STT/TTS |
| Complaint Microservice | http://localhost:8002 | Person 3 Civic Grievance & SLA Engine |

Open http://localhost:3000 in your browser once services are running.

> **First time only** — install dependencies before running:
> ```powershell
> # 1. AI Agent Backend
> cd nagrik-agent-backend
> pip install -r requirements.txt
>
> # 2. Complaint Backend (Person 3)
> cd ../backend/complaint_service
> pip install -r requirements.txt
>
> # 3. Frontend
> cd ../../frontend
> npm install
> ```

---

## Manual startup (if you prefer separate terminals)

**Terminal 1 — Backend:**
```powershell
cd nagrik-agent-backend
py -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

**Terminal 2 — Frontend:**
```powershell
cd frontend
npm run dev
```

---

## Environment setup

Copy and fill in the backend `.env`:
```powershell
copy nagrik-agent-backend\.env.example nagrik-agent-backend\.env
# Then edit .env and set:
#   OPENROUTER_API_KEY=...
#   SARVAM_API_KEY=...
```

---

## Repository Structure

```
Nagrik/
├── nagrik-agent-backend/     # PRIMARY AI backend (FastAPI + LangGraph)
│   ├── app/api/              # REST endpoints: /chat /chat/voice /complaints /health
│   ├── app/graph/            # LangGraph agent: router → responder → tools → navigation
│   ├── app/rag/              # Tree-RAG retrieval over ChromaDB
│   ├── app/multilingual/     # Sarvam STT / TTS / translation
│   └── app/integrations/     # Client stubs for external services
│
├── frontend/                 # Next.js citizen & government portal
│
├── backend/complaint_service/ # Standalone complaint microservice (PostgreSQL, optional)
├── ingestion/                # Data pipeline: PDFs → ChromaDB embeddings
├── schemes_api/              # Legacy scheme API (not primary)
└── docs/                     # INTEGRATION_PLAN.md · INTEGRATION_STATUS.md
```
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
