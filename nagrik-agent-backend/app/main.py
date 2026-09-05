"""
FastAPI entry point. Mounts all routers; nothing agent-specific lives here.
"""
import sys
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.api import chat, applications, health, complaints, schemes, crawler
from fastapi.middleware.cors import CORSMiddleware
from app.crawler.scheduler import start_crawler_scheduler, stop_crawler_scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: launch 24-hour background crawler scheduler
    try:
        start_crawler_scheduler()
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Could not initialize crawler scheduler: {e}")
    yield
    # Shutdown: clean up background workers
    try:
        stop_crawler_scheduler()
    except Exception as e:
        pass

app = FastAPI(title="Nagrik - AI Agent & Voice/Application Backend", lifespan=lifespan)

app.include_router(health.router, tags=["health"])
app.include_router(chat.router, tags=["chat"])
app.include_router(applications.router, tags=["applications"])
app.include_router(complaints.router, tags=["complaints"])
app.include_router(schemes.router, tags=["schemes"])
app.include_router(crawler.router, tags=["crawler"])

import os

cors_origins_raw = os.environ.get("CORS_ORIGINS", "")
allowed_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
if cors_origins_raw:
    allowed_origins.extend([o.strip() for o in cors_origins_raw.split(",") if o.strip()])

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"https?://.*" if not cors_origins_raw else None,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)