# Nagrik — AI Agent & Voice/Application Backend (Person 2)

Central LangGraph-based conversational agent for the Nagrik Digital Citizen
Companion (SIH). Handles text + voice + image/document understanding,
conversation memory, intent detection, tool calling, and Tree-RAG over
government scheme knowledge.

## Quick start

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in your API keys
uvicorn app.main:app --reload --port 8000
```

Open `http://localhost:8000/docs` for interactive API docs.

## Switching LLM providers (no code changes)

Edit `.env`:
```
LLM_PROVIDER=openrouter   # for development
LLM_MODEL=openai/gpt-4o-mini
OPENROUTER_API_KEY=...
```
For the demo:
```
LLM_PROVIDER=gemini
LLM_MODEL=gemini-1.5-flash
GEMINI_API_KEY=...
```
Every node calls `get_llm()` from `app/llm/get_llm.py` — never a provider SDK
directly — so this swap is the ONLY change needed.

## Ingesting Tree-RAG documents

Drop `.txt` files under:
```
data/govt_docs/<ministry>/<department>/<scheme_name>.txt
```
Then run:
```bash
python -m app.rag.ingest
```
This chunks, embeds (via `sentence-transformers`, downloaded on first run —
needs internet access), and stores them in a local Chroma DB at
`./data/chroma_store`.

## Running tests

```bash
pip install pytest pytest-asyncio
pytest app/tests/ -v
```

`test_provider_swap.py` should be run once with `LLM_PROVIDER=openrouter`
and once with `LLM_PROVIDER=gemini` before the demo, per the project's
Milestone 6 definition of done.

## Key endpoints

| Endpoint | Purpose |
|---|---|
| `GET /health` | Sanity check + shows active LLM provider/model |
| `POST /chat` | Text chat (+ optional image/document attachment) |
| `POST /chat/voice` | Audio in → Sarvam STT → graph → Sarvam TTS → audio out |
| `POST /applications/scholarship/continue` | Drives the sample form-filling flow |

## Design notes / where things live

- `app/llm/get_llm.py` — the ONLY place provider SDKs are imported.
- `app/graph/build_graph.py` — the central LangGraph agent (router → responder ⇄ tools → navigation).
- `app/graph/nodes/form_filler.py` — application flow. Modality-agnostic: only ever sees text/structured data, never audio or images directly.
- `app/graph/nodes/doc_understanding.py` — image/document field extraction, merges into `extracted_fields`.
- `app/multilingual/language_boundary.py` — STT/translate in, translate/TTS out. Sits OUTSIDE the core graph so intent detection/tools/RAG stay language-agnostic.
- `app/rag/` — Tree-RAG: hierarchy-aware chunking (ministry → department → scheme), Chroma storage, hierarchical + vector retrieval, honest "not found" instead of hallucination.
- `app/integrations/person1_client.py`, `person3_client.py` — HTTP clients with a `USE_MOCK_BACKENDS` switch so you're never blocked waiting on their real APIs.

## Known gaps / TODOs before demo

- `app/voice/twilio_webhook.py` is a stub — fill in if time allows after the core text/voice-over-web flow is solid.
- Confirm exact Sarvam API request/response shape against current docs (`app/multilingual/sarvam_client.py` has a note on this) — API versions can change field names.
- Agree the `citizen_id`/`session_id` format with Person 1 & 3 and update `person1_client.py`/`person3_client.py` once their real endpoints are live (flip `USE_MOCK_BACKENDS=false`).
- Decide complaint-classification ownership with Person 3 (recommendation: this agent extracts raw fields only; Person 3's backend classifies/routes — already reflected in `complaint_tools.py`'s docstring).
