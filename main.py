import os
import json
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

from backend.db.database import engine, Base
from backend.api.routes.sessions import router as sessions_router
from backend.api.routes.voice import router as twilio_router

# Create DB tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Nagrik Voice Form System")

# ---------- Routers ----------
app.include_router(sessions_router, prefix="/api/sessions", tags=["sessions"])
app.include_router(twilio_router, prefix="/api/twilio", tags=["twilio"])

# ---------- Convenience alias used by the existing web UI ----------
# The old HTML calls POST /api/chat — we forward it to /api/sessions/chat
from backend.api.routes.sessions import chat_api, ChatRequest
from fastapi import Depends
from backend.db.database import get_db
from sqlalchemy.orm import Session

@app.post("/api/chat")
async def chat_alias(req: ChatRequest, db: Session = Depends(get_db)):
    """Alias kept for backward-compatibility with the existing Web UI."""
    return chat_api(req, db)

# ---------- Forms discovery ----------
SCHEMAS_DIR = os.path.join(os.path.dirname(__file__), "schemas")

@app.get("/api/forms")
def list_forms():
    """List all available JSON schemas."""
    forms = []
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
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Schema not found")
    with open(fpath, encoding="utf-8") as f:
        return json.load(f)

# ---------- Frontend ----------
@app.get("/", response_class=HTMLResponse)
def read_root():
    try:
        with open(os.path.join(os.path.dirname(__file__), "templates", "index.html"), encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "<html><body><h1>Templates folder not found!</h1></body></html>"

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)
