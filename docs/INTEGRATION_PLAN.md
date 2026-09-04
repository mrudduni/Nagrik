# NAGRIK — Integration Plan

Generated: 2026-09-04

---

## 1. Current Architecture

```
Browser / Next.js (port 3000)
        │
        │  HTTP to http://127.0.0.1:8000
        ▼
nagrik-agent-backend/    ← PRIMARY AI BACKEND (FastAPI + LangGraph)
├── app/api/chat.py          POST /chat, POST /chat/voice
├── app/api/applications.py  POST /applications/scholarship/continue
├── app/api/health.py        GET /health
├── app/graph/
│   ├── build_graph.py       LangGraph StateGraph (compiled once)
│   ├── nodes/router.py      Intent detection (LLM structured output)
│   ├── nodes/responder.py   ReAct tool-calling node
│   ├── nodes/navigation.py  NavigationAction decision node
│   ├── nodes/doc_understanding.py  Vision LLM / PyMuPDF for images+PDFs
│   ├── nodes/form_filler.py Application field extraction + prompt
│   └── tools/
│       ├── rag_tools.py     tree_rag_search (Tree-RAG over ChromaDB)
│       ├── scheme_tools.py  query_schemes, check_eligibility, compare_schemes
│       └── complaint_tools.py  file_complaint, check_complaint_status  ← MOCK
├── app/rag/retriever.py     Hybrid vector+keyword Tree-RAG retrieval
├── app/rag/store.py         ChromaDB persistence wrapper
├── app/multilingual/
│   ├── language_boundary.py STT→pivot→TTS language edge
│   └── sarvam_client.py     Sarvam STT, TTS, translate
├── app/memory/checkpointer.py  MemorySaver (in-process per session_id)
├── app/integrations/
│   ├── person3_client.py    HTTP client for complaint backend (MOCK active)
│   └── person1_client.py    HTTP client for scheme backend (MOCK active)
└── app/schemas/
    ├── chat.py              ChatRequest/Response/Source/NavigationAction
    ├── agent_state.py       AgentState TypedDict
    └── forms.py             FormSchema, SAMPLE_SCHOLARSHIP_FORM

backend/complaint_service/  ← SEPARATE COMPLAINT SERVICE (needs PostgreSQL)
├── app/services/classifier.py    LLM→ML→Keyword hybrid classifier
├── app/services/priority_scorer.py  Score/tier calculation
├── app/services/router.py           Department routing (DB-backed)
├── app/services/duplicate_detector.py  FAISS similarity
├── app/services/resolution.py
├── app/services/escalation.py
├── app/services/sla_monitor.py
└── app/models/complaint.py          SQLAlchemy async models

frontend/src/
├── services/chat-service.ts      sendMessage, sendVoiceMessage → POST /chat
├── services/issue-service.ts     listIssues, reportIssue → MOCK in-memory
├── services/application-service.ts → MOCK in-memory
├── services/scheme-service.ts    → MOCK in-memory (MOCK_SCHEMES)
├── services/_client.ts           API_URL=http://127.0.0.1:8000
├── context/app-provider.tsx      session, language, notifications
├── components/citizen/chat/      ChatPanel, ChatComposer, ChatMessageBubble
├── app/(citizen)/page.tsx        Home with ChatPanel + HomeWidgets
├── app/(citizen)/issues/         Civic issues pages (uses issue-service MOCK)
├── app/(citizen)/applications/   Applications pages (uses app-service MOCK)
└── app/(citizen)/services/       Schemes browse (uses scheme-service MOCK)
```

---

## 2. Working Features (Preserve All)

| Feature | File(s) | Status |
|---------|---------|--------|
| Text chat | chat-service.ts → /chat | ✅ Working |
| Voice chat (STT+TTS) | /chat/voice, sarvam_client.py | ✅ Working |
| Multilingual (hi/ta/mr/bn/gu/kn/ml) | language_boundary.py | ✅ Working |
| Image upload + vision LLM | doc_understanding_node, chat.py | ✅ Working |
| PDF upload + PyMuPDF extraction | doc_understanding_node | ✅ Working |
| Tree-RAG scheme retrieval | retriever.py, rag_tools.py | ✅ Working |
| Source metadata in response | _extract_sources(), ChatSource | ✅ Working |
| LangGraph intent routing | router.py, build_graph.py | ✅ Working |
| Navigation actions (JSON) | navigation.py | ✅ Produced, not consumed by frontend |
| Form filler node | form_filler.py | ✅ Working (demo) |
| Session memory (in-process) | MemorySaver + thread_id | ✅ Per-restart |
| Frontend CORS | main.py | ✅ Working |

---

## 3. Problems Identified

### Critical / User-Visible
1. **complaint_tools.py uses mock** — `person3_client` always returns fake IDs; the real complaint service needs PostgreSQL + FAISS to run.
2. **Frontend session_id is hardcoded `"frontend-session"`** — every user shares the same conversation context.
3. **Source cards show only label="Government Source" href="#"** — ChatSource rich fields (scheme, ministry, snippet) exist in backend response but `mapSources()` in chat-service.ts ignores them.
4. **NavigationAction returned by backend is never consumed** — frontend does not read `navigation` field from API response.
5. **issue-service.ts is fully mock** — `reportIssue`, `classifyIssueText`, `listIssues` use in-memory store; voice transcription in new-issue page is hardcoded canned text.
6. **scheme-service.ts is fully mock** — uses MOCK_SCHEMES, never calls Tree-RAG.
7. **application-service.ts is fully mock** — no connection to form_filler_node or /applications endpoint.
8. **No error boundaries for backend unavailable**.
9. **HTTPException missing import in chat.py** for voice endpoint.

### Minor
10. `lru_cache` on `get_llm(temperature=...)` will reuse wrong instances if different temperatures are needed.
11. complaint_service needs PostgreSQL — not trivially runnable for hackathon without DB.
12. Sarvam voice on issues page is a hardcoded setTimeout stub.

---

## 4. Integration Points

### Phase 3 — Complaint service (self-contained, no PostgreSQL required for hackathon)
- Create `nagrik-agent-backend/app/tools/complaint_tools.py` (the EXISTING file at `graph/tools/complaint_tools.py`)
- Inline the classifier and priority_scorer logic from `backend/complaint_service/app/services/` directly into the tool layer — no DB needed for classification
- Store complaints in an in-memory dict keyed by complaint_id for status lookup (sufficient for hackathon)
- Generate `NGR-XXXX` format IDs

### Phase 4 — Application tools
- Expose form_filler_node as a proper graph tool
- Route intent=application to form_filler with detected schema

### Phase 5 — LangGraph routing
- Ensure complaint intent → complaint tools (already wired, needs real tools)
- Add application intent routing through form_filler

### Phase 6 — Source cards
- Update `mapSources()` in chat-service.ts to return rich ChatSource fields
- Update ChatMessageBubble to render scheme/ministry/snippet

### Phase 7 — Navigation
- Read `navigation` field in chat-service.ts response
- Emit navigation events from ChatPanel to router

### Phase 8 — Session memory
- Generate stable session_id in ChatPanel using useRef/localStorage

### Phase 9 — Error handling
- Wrap backend calls with user-friendly error display
- Fix missing HTTPException import in chat.py

### Phases 10–11 — Mock removal / validation
- Replace chat-service mapSources with real field mapping
- Add MIME + size validation in chat.py and chat-composer.tsx

---

## 5. Files That Must Not Be Modified

| File | Reason |
|------|--------|
| nagrik-agent-backend/app/rag/retriever.py | Core Tree-RAG logic — working |
| nagrik-agent-backend/app/rag/store.py | ChromaDB layer |
| nagrik-agent-backend/app/multilingual/sarvam_client.py | Sarvam STT/TTS/translate |
| nagrik-agent-backend/app/multilingual/language_boundary.py | Language detection pipeline |
| nagrik-agent-backend/app/graph/nodes/doc_understanding.py | Vision LLM / PDF extraction |
| nagrik-agent-backend/app/memory/checkpointer.py | Session persistence |
| nagrik-agent-backend/app/llm/get_llm.py | LLM provider abstraction |
| nagrik-agent-backend/app/graph/build_graph.py | LangGraph wiring |
| frontend/src/services/_client.ts | API client base |
| frontend/tailwind.config / postcss.config | UI build |

---

## 6. Risks / Conflicts

| Risk | Mitigation |
|------|-----------|
| complaint_service needs PostgreSQL+FAISS | Use self-contained classifier inline; in-memory complaint store for hackathon |
| LangGraph MemorySaver is per-process restart | Document clearly; sufficient for demo |
| Sarvam API rate limits | Existing fallback mechanism intact |
| ChromaDB not seeded = empty RAG | Must run ingestion before demo |
| lru_cache temperature conflict | Non-critical for demo (temperature 0/0.3 used) |
