import os
import json
import sys
import importlib
from typing import Any
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy.orm import Session

# Add current directory and nagrik-agent-backend to sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

NAGRIK_AGENT_DIR = os.path.join(BASE_DIR, "nagrik-agent-backend")
if NAGRIK_AGENT_DIR not in sys.path:
    sys.path.insert(0, NAGRIK_AGENT_DIR)

from backend.db.database import engine, Base, get_db
from backend.api.routes.sessions import router as sessions_router, chat_api, ChatRequest
from backend.api.routes.voice import router as twilio_router

# Create DB tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Nagrik Voice Form & AI Agent System")

# ---------- CORS Middleware (crucial for frontend Next.js on localhost:3000) ----------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Core Base Routers ----------
app.include_router(sessions_router, prefix="/api/sessions", tags=["sessions"])
app.include_router(twilio_router, prefix="/api/twilio", tags=["twilio"])

# ---------- Agent Backend Routers (chat, voice, complaints, applications, health) ----------
try:
    from app.api import chat, applications, health, complaints

    # Support all endpoint prefixes (/chat, /api/chat, /api/v1/chat)
    for prefix in ("", "/api", "/api/v1"):
        app.include_router(health.router, prefix=prefix, tags=["health"])
        app.include_router(chat.router, prefix=prefix, tags=["chat"])
        app.include_router(applications.router, prefix=prefix, tags=["applications"])
        app.include_router(complaints.router, prefix=prefix, tags=["complaints"])

    print("[Info] Successfully mounted Nagrik Agent backend routers at root, /api, and /api/v1")
except Exception as e:
    print(f"[Warning] Could not load nagrik-agent-backend routers: {e}")


# ---------- Forms discovery ----------
SCHEMAS_DIR = os.path.join(BASE_DIR, "schemas")

@app.get("/api/forms")
def list_forms():
    """List all available JSON schemas."""
    forms = []
    if os.path.exists(SCHEMAS_DIR):
        for fname in os.listdir(SCHEMAS_DIR):
            if fname.endswith(".json"):
                schema_id = fname[:-5]
                fpath = os.path.join(SCHEMAS_DIR, fname)
                with open(fpath, encoding="utf-8") as f:
                    schema = json.load(f)
                forms.append({
                    "id": schema_id,
                    "name": schema.get("name", schema_id),
                    "description": schema.get("description", ""),
                    "issuing_authority": schema.get("issuing_authority", ""),
                })
    return forms

@app.get("/api/forms/{schema_id}/schema")
def get_schema(schema_id: str):
    """Return the raw JSON schema for a form."""
    fpath = os.path.join(SCHEMAS_DIR, f"{schema_id}.json")
    if not os.path.exists(fpath):
        raise HTTPException(status_code=404, detail="Schema not found")
    with open(fpath, encoding="utf-8") as f:
        return json.load(f)

# ---------- Frontend fallback ----------
@app.get("/", response_class=HTMLResponse)
def read_root():
    try:
        with open(os.path.join(BASE_DIR, "templates", "index.html"), encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "<html><body><h1>Nagrik Backend is running!</h1></body></html>"

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

