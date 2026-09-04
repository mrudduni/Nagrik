# NAGRIK — Integration Status

Generated: 2026-09-04

---

## DONE

### Backend (nagrik-agent-backend)

- **HTTPException import fixed** in `app/api/chat.py` — voice endpoint no longer crashes on import
- **Input validation** in `app/api/chat.py`:
  - Attachment MIME type checked (image/jpeg,png,gif,webp,heic; application/pdf)
  - Attachment base64 size capped at 10 MB (~14 M chars)
  - Audio base64 size capped on `/chat/voice`
  - Empty message+attachment rejected with 400
  - Graceful 503 returned when LLM or STT is unavailable
  - Internal paths stripped from `source_file` in `_extract_sources()`
- **Complaint tools** (`app/graph/tools/complaint_tools.py`) — fully self-contained:
  - Keyword+rule classifier (same logic as `backend/complaint_service`)
  - Priority scorer (CRITICAL/HIGH/MEDIUM/LOW tiers)
  - `NGR-XXXXXX` reference ID generation
  - In-memory complaint store (shared between agent tools and REST API)
  - `file_complaint` and `check_complaint_status` LangChain tools
- **Application tools** (`app/graph/tools/application_tools.py`):
  - `start_application` — starts assisted draft, returns missing fields
  - `update_application` — merges new field values, asks for next missing field
  - `get_application_status` — retrieves draft by `APP-XXXXXX` ID
  - Scheme-specific field maps (PM-KISAN, scholarship, Ayushman Bharat, default)
- **LangGraph responder** (`app/graph/nodes/responder.py`):
  - All 9 tools registered: `query_schemes`, `check_eligibility`, `compare_schemes`, `file_complaint`, `check_complaint_status`, `start_application`, `update_application`, `get_application_status`, `tree_rag_search`
  - SYSTEM_PROMPT includes full COMPLAINT FLOW and APPLICATION FLOW instructions
  - Citizen ID and extracted document fields injected as context before tool calls
- **Router** (`app/graph/nodes/router.py`):
  - Expanded INTENT_SYSTEM_PROMPT with Hindi/Hinglish complaint examples
  - All 5 intents with concrete examples including `NGR-*` and `APP-*` status checks
- **Complaints REST API** (`app/api/complaints.py`):
  - `POST /complaints/classify` — classify text, return category/severity/dept
  - `POST /complaints` — file complaint, return `NGR-XXXXXX` ID
  - `GET /complaints` — list all complaints for a citizen ID
  - `GET /complaints/{id}` — get single complaint status
- **main.py** — complaints router mounted alongside health/chat/applications
- **health.py** — now returns registered tools list, RAG config, checkpointer type

### Frontend (Next.js)

- **Stable session ID** (`chat-panel.tsx`):
  - `getOrCreateSessionId()` using `sessionStorage` keyed by `nagrik.chat.session_id`
  - Persists across navigation within the same browser tab
  - New ID created per tab/session, not per request
- **Navigation actions** (`chat-panel.tsx`):
  - `useNavigationAction()` hook handles all 5 action types
  - `open_scheme_page` → `/services/{id}` or `/services`
  - `open_comparison` → `/services/compare`
  - `open_application_form` → `/apply/{id}` or `/services`
  - `open_complaint_status` → `/issues`
  - `open_profile` → `/profile`
- **Rich source cards** (`chat-message-bubble.tsx`):
  - Scheme name (bold), ministry/department (sublabel), page reference, 2-line snippet
  - External link icon shown only for genuine http(s) URLs
  - Internal filesystem paths / Chroma paths never displayed
- **Source mapping** (`chat-service.ts`):
  - `mapSources()` maps `scheme`, `ministry`, `department`, `page`, `snippet`, `source_url`
  - Falls back gracefully to legacy `title`/`content` fields
  - `sendMessage()` returns `navigation`, `intent`, `extractedFields`
- **`ChatSource` type** (`types/index.ts`):
  - Added `sublabel`, `pageRef`, `snippet` optional fields
- **Issue service** (`issue-service.ts`):
  - `classifyIssueText()` calls real `POST /complaints/classify` with keyword fallback
  - `reportIssue()` calls real `POST /complaints`, falls back to mock store if backend unavailable
  - `listIssues()` fetches `GET /complaints?citizen_id=<id>` and merges with mock data
  - `getIssue()` fetches `GET /complaints/{id}` for NGR-prefixed IDs, falls back to mock
- **Voice on new issue page** (`issues/new/page.tsx`):
  - Replaced hardcoded canned transcript with real MediaRecorder → Sarvam STT
  - Uses `/chat/voice` endpoint via `sendVoiceMessage()`
  - Auto-stops after 10 seconds
  - Gracefully falls back to typed input if microphone unavailable
- **Location detect** (`issues/new/page.tsx`):
  - Uses `navigator.geolocation` API
  - Falls back to citizen profile address if geolocation denied
- **File validation** (`chat-composer.tsx`):
  - 10 MB size check before base64 conversion
  - MIME type whitelist (JPEG/PNG/GIF/WebP for images; PDF for documents)
  - Empty voice recording shows user-friendly alert instead of silently failing
- **Error messages** (`chat-panel.tsx`):
  - `makeErrorMessage()` maps timeout/network/500/400 errors to citizen-friendly text
  - Stack traces never shown to citizens

---

## PARTIALLY DONE

- **`listIssues` nearby filter** — fetches citizen's own complaints from backend, but "Nearby Reports" tab still uses mock data (no geo-based complaint query on backend)
- **Application service** (`application-service.ts`) — `createApplication`, `saveDraftApplication`, `listApplications`, `getApplication` still use in-memory mock store; not wired to `/applications` backend endpoint (the backend `/applications/scholarship/continue` is for the agent-assisted flow, not direct CRUD)
- **Scheme service** (`scheme-service.ts`) — `listSchemes`, `getScheme`, `checkEligibility` use mock data; Tree-RAG answers scheme questions through the agent chat but scheme browse pages do not call Tree-RAG directly
- **`issues/[id]` SLA timer** — `hoursElapsed` is computed at load time; does not update live

---

## NOT IMPLEMENTED

- **Real government submission** — Application drafts are local only. No actual ministry portal API exists to submit to. Clearly labelled as drafts.
- **DigiLocker / eSign integration** — Not available; UI shows placeholder
- **Push notifications** — notification-service.ts is mock; no real-time backend
- **Profile sync with backend** — auth-service.ts is mock; no real login/JWT
- **Scheme browse from Tree-RAG** — `/services` page uses mock scheme cards; Tree-RAG is only accessible through the chat agent
- **Real-time complaint tracking** — In-memory store resets on backend restart; a database backend would make this persistent
- **Duplicate detection** — complaint_service's FAISS-based deduplicator requires PostgreSQL; not enabled
- **n8n workflow integration** — `n8n_client.py` exists but no live n8n instance assumed

---

## KNOWN LIMITATIONS

1. **In-memory stores reset on backend restart** — Complaints and application drafts filed via the agent are lost when the backend process restarts. For a production system, replace with a persistent database.
2. **MemorySaver conversation context** — LangGraph session memory is per-process; restarting the backend starts all conversations fresh.
3. **ChromaDB must be seeded** — If `./data/chroma_store` is empty, Tree-RAG will return no results. Run the ingestion pipeline before demo.
4. **Sarvam API key required** — Voice STT/TTS and translation are disabled if `SARVAM_API_KEY` is not set. Text chat still works.
5. **OpenRouter API key required** — LLM calls fail without `OPENROUTER_API_KEY`. Set in `nagrik-agent-backend/.env`.
6. **`USE_MOCK_BACKENDS=true`** — By default, `person1_client` (scheme backend) and `person3_client` (legacy complaint backend) use mock responses. The self-contained complaint tools do not depend on this flag.

---

## TEST RESULTS

### Frontend build
```
✓ Compiled successfully
✓ TypeScript: 0 errors
✓ 16 routes generated (static + dynamic)
```

### Backend imports
```
✓ ALL_TOOLS = [query_schemes, check_eligibility, compare_schemes,
               file_complaint, check_complaint_status,
               start_application, update_application, get_application_status,
               tree_rag_search]
✓ /complaints routes: classify, POST /, GET /, GET /{id}
```

### Complaint tool (unit)
```
file_complaint("test-user", "huge pothole near college", "MG Road")
→ complaint_id: NGR-B6D266, category: Pothole, priority: LOW,
  department: Municipal Corporation — Roads & Infrastructure, sla_hours: 120

check_complaint_status("NGR-B6D266")
→ found: True, status: SUBMITTED, department: ..., sla_hours: 120
```

### Application tool (unit)
```
start_application("u1", "scholarship", {full_name: "Raj Kumar"})
→ APP-33EA9F, next_question: "Could you share your aadhaar number?"

update_application("APP-33EA9F", {all remaining fields})
→ status: READY_TO_SUBMIT, fields_missing: []
```

### Manual verification required (needs running backend + Sarvam key)
- [ ] English text: "What is Aam Aadmi Bima Yojana?"
- [ ] Hindi: "आम आदमी बीमा योजना क्या है?"
- [ ] Hinglish: "Mujhe kisan ke liye schemes batao"
- [ ] Voice chat (STT → agent → TTS)
- [ ] Image upload → vision understanding
- [ ] PDF upload → text extraction
- [ ] Complaint: "There is a pothole near my college" → NGR ID
- [ ] Status: "Track my complaint NGR-XXXXXX"
- [ ] Application: "I want to apply for PM KISAN" → guided fields
- [ ] Document-assisted application: upload Aadhaar → pre-filled fields
- [ ] Navigation: scheme page, application form, complaint status
