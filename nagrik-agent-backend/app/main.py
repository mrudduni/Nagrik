"""
FastAPI entry point. Mounts all routers; nothing agent-specific lives here.
"""
from fastapi import FastAPI
from app.api import chat, applications, health, complaints, schemes
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Nagrik - AI Agent & Voice/Application Backend")

app.include_router(health.router, tags=["health"])
app.include_router(chat.router, tags=["chat"])
app.include_router(applications.router, tags=["applications"])
app.include_router(complaints.router, tags=["complaints"])
app.include_router(schemes.router, tags=["schemes"])

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