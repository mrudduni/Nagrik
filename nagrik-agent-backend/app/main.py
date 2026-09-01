"""
FastAPI entry point. Mounts all routers; nothing agent-specific lives here.
"""
from fastapi import FastAPI
from app.api import chat, applications, health

app = FastAPI(title="Nagrik - AI Agent & Voice/Application Backend")

app.include_router(health.router, tags=["health"])
app.include_router(chat.router, tags=["chat"])
app.include_router(applications.router, tags=["applications"])
