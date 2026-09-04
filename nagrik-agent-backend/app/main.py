"""
FastAPI entry point. Mounts all routers; nothing agent-specific lives here.
"""
from fastapi import FastAPI
from app.api import chat, applications, health, complaints
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Nagrik - AI Agent & Voice/Application Backend")

app.include_router(health.router, tags=["health"])
app.include_router(chat.router, tags=["chat"])
app.include_router(applications.router, tags=["applications"])
app.include_router(complaints.router, tags=["complaints"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)