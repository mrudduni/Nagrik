# Nagrik Complaint & Grievance Backend (Person 3 — Gargi)

**Track:** BHARAT PRAGATI (AI for Cybersecurity, FinTech & Digital Governance)  
**Problem Statement:** PS3 — Digital Citizen Assistant for Multilingual Access to Government Services & Schemes  
**Role:** Person 3 (Gargi) — Complaint & Grievance Microservice  

The Complaint Service is an intelligent civic accountability engine that turns citizen complaints into trackable, prioritized, and auditable government workflows. It manages the complete lifecycle: **submission → classification → duplicate detection → prioritization → routing → SLA tracking → escalation → resolution verification**.

---

## 🏛️ Features & Architecture

```
Citizen Input (Voice / Text / Image)
                 ↓
      [Person 2 Agent Backend]
                 ↓  (POST /api/v1/complaints)
   [Complaint Classification] ──→ LLM Structured Output (Gemini / OpenRouter)
                 ↓                + scikit-learn NaiveBayes / Keyword Fallback
  [Semantic Vector Embedding] ──→ sentence-transformers (all-MiniLM-L6-v2) + FAISS
                 ↓
     [Duplicate Detection]   ──→ FAISS Cosine Similarity + Haversine Proximity
                 ↓
       [Priority Scoring]     ──→ Weighted Formula (Severity × Cluster Size × Age)
                 ↓
      [Department Routing]    ──→ Automated Routing to 15+ Municipal / State Authorities
                 ↓
    [Resolution State Machine]──→ Submitted → Acknowledged → Assigned → In-Progress
                 ↓                → Resolution Claimed → Citizen Verified → Closed
      [SLA Monitor & Engine]  ──→ Background SLA checks + multi-tier escalation (Levels 1-3)
                 ↓
      [n8n Webhook Alerts]    ──→ Notification workflows on escalation, SLA breach & updates
```

---

## 🛠️ Tech Stack

- **Framework**: FastAPI (Python 3.10+)
- **Database**: PostgreSQL with SQLAlchemy 2.0 (AsyncIO + asyncpg)
- **Vector Search**: FAISS (`IndexFlatIP` for cosine similarity)
- **Embeddings**: `sentence-transformers/all-MiniLM-L6-v2`
- **Machine Learning**: scikit-learn (TF-IDF + Naive Bayes fallback)
- **LLM Engine**: OpenRouter / Google Gemini 2.0 Flash (via httpx)
- **Workflow Automation**: n8n Webhook integrations
- **Scheduler**: APScheduler for periodic SLA monitoring
- **Containerization**: Docker & Docker Compose

---

## 🚀 Quick Start

### 1. Prerequisites & Environment Setup

```bash
cd backend/complaint_service
python -m venv venv
venv\Scripts\activate  # Windows: venv\Scripts\activate (Linux/Mac: source venv/bin/activate)
pip install -r requirements.txt
```

Create a `.env` file (copied from `.env.example`):
```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/nagrik_complaints
LLM_PROVIDER=openrouter
LLM_MODEL=google/gemini-2.0-flash-001
OPENROUTER_API_KEY=your_key_here
GEMINI_API_KEY=your_key_here
EMBEDDING_MODEL=all-MiniLM-L6-v2
FAISS_INDEX_PATH=data/faiss_index.bin
N8N_WEBHOOK_URL=https://your-n8n-instance.com/webhook/nagrik-alerts
DEFAULT_ACK_SLA_HOURS=24
DEFAULT_RESOLUTION_SLA_HOURS=168
SLA_CHECK_INTERVAL_MINUTES=15
DUPLICATE_SIMILARITY_THRESHOLD=0.80
```

### 2. Run Database & Service via Docker Compose

```bash
docker-compose up -d postgres
```

### 3. Seed Realistic Indian Municipal Data

Populates **15 Indian municipal departments** (BBMP, PWD, DJB, BMC, BESCOM, BMTC, etc.), **SLA configurations**, and **50 realistic civic complaints** across Bangalore, Delhi, Mumbai, Chennai, and Kolkata:

```bash
python -m scripts.seed_data
```

### 4. Start the Application

```bash
python run.py
# Or: uvicorn app.main:app --reload --port 8002
```

Swagger API Docs: [http://localhost:8002/docs](http://localhost:8002/docs)  
ReDoc: [http://localhost:8002/redoc](http://localhost:8002/redoc)

---

## 📡 API Endpoints Reference

All endpoints are prefixed with `/api/v1`:

### 1. Complaints (`/api/v1/complaints`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/complaints/` | Submit new complaint (runs classify, duplicate check, priority scoring, routing, SLA) |
| `GET` | `/complaints/` | List complaints with pagination and filters (`status`, `category`, `severity`, `citizen_id`) |
| `GET` | `/complaints/{id}` | Get full complaint details with event timeline and evidence |
| `GET` | `/complaints/{id}/status` | Lightweight status check (designed for Person 2 agent backend) |
| `PATCH`| `/complaints/{id}/status` | Transition status with state-machine validation |
| `POST` | `/complaints/{id}/verify` | Citizen accepts (closes) or rejects (reopens/escalates) resolution |
| `POST` | `/complaints/{id}/evidence` | Attach photo/document evidence |
| `GET` | `/complaints/{id}/timeline` | Get auditable event timeline |
| `GET` | `/complaints/{id}/similar` | Find duplicates / similar issues using FAISS vector search |

### 2. Clusters (`/api/v1/clusters`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/clusters/` | List active complaint clusters grouped by issue & geographic density |
| `GET` | `/clusters/{id}` | View cluster details and all member complaints |
| `POST` | `/clusters/rerun` | Trigger manual DBSCAN re-clustering |

### 3. Government Analytics (`/api/v1/analytics`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/analytics/overview` | High-level KPIs (total, open, resolved, avg resolution time, SLA compliance rate) |
| `GET` | `/analytics/departments`| Department-wise performance metrics and pendency |
| `GET` | `/analytics/categories` | Distribution and average severity across categories |
| `GET` | `/analytics/trends` | Time-series complaint influx |
| `GET` | `/analytics/sla` | Department-wise SLA compliance and breach reports |

### 4. Officer / Admin Actions (`/api/v1/admin`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/admin/complaints/{id}/acknowledge` | Authority marks complaint as acknowledged |
| `POST` | `/admin/complaints/{id}/assign` | Assign complaint to field engineer/officer |
| `POST` | `/admin/complaints/{id}/resolve` | Claim resolution and prompt citizen verification |
| `GET` | `/admin/departments/{id}/queue` | View active department workload queue |
| `GET` | `/admin/health` | Database connectivity check |

---

## 🧪 Running Tests

```bash
pytest tests/ -v
```

Tests cover:
- Hybrid and rule-based classification
- Haversine distance math
- Priority scoring algorithms and clamping
- Resolution state machine transitions
- Department jurisdiction routing

---

## 🤝 Integration Contracts

- **For Person 2 (Navya — Agent Backend):**
  - Submit complaint: `POST /api/v1/complaints/`
  - Check status: `GET /api/v1/complaints/{id}/status`
- **For Frontend Person 2 (Gargi — Gov Dashboard):**
  - KPI & Heatmap Analytics: `GET /api/v1/analytics/overview`, `/api/v1/analytics/departments`, `/api/v1/clusters/`
  - Action Panels: `POST /api/v1/admin/complaints/{id}/assign`, `/resolve`
- **For n8n Automation:**
  - Configurable webhook dispatch for `ESCALATION`, `SLA_BREACH`, and `STATUS_UPDATE` events.
