"""
FastAPI entry point. Mounts all routers; nothing agent-specific lives here.
"""
from fastapi import FastAPI
from app.api import chat, applications, health, complaints
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Nagrik - AI Agent & Voice/Application Backend")

# Support all common URL prefixes (/chat, /api/chat, /api/v1/chat)
for prefix in ("", "/api", "/api/v1"):
    app.include_router(health.router, prefix=prefix, tags=["health"])
    app.include_router(chat.router, prefix=prefix, tags=["chat"])
    app.include_router(applications.router, prefix=prefix, tags=["applications"])
    app.include_router(complaints.router, prefix=prefix, tags=["complaints"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)