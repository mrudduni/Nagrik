# NAGRIK Deployment Guide

This guide explains how to deploy NAGRIK (Next.js Frontend + FastAPI Agent Backend) to production.

---

## Architecture Overview
- **Frontend**: Next.js 16 (App Router + TailwindCSS)
- **Backend**: FastAPI (Python 3.11/3.14) + LangGraph + Sarvam AI / Gemini Speech + Tavily Crawler
- **Databases**: Neo4j Aura (Knowledge Graph) + Supabase (Auth/Relational)

---

## Option 1: Vercel (Frontend) + Render / Railway (Backend) — *Recommended for Hackathons*

### 1. Deploy the Backend (Render.com or Railway.app)
1. Go to [Render.com](https://render.com) and click **New +** -> **Web Service**.
2. Connect your GitHub repository: `https://github.com/mrudduni/Nagrik`.
3. Configure settings:
   - **Root Directory**: `nagrik-agent-backend`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install --upgrade pip && pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Add Environment Variables from `nagrik-agent-backend/.env`:
   - `LLM_PROVIDER`: `gemini`
   - `LLM_MODEL`: `gemini-3.5-flash-lite`
   - `GEMINI_API_KEY`: *(your Gemini key)*
   - `SARVAM_API_KEY`: `sk_7g094gnv_qNO5KVj8ocN1dKifLU6oG5MS`
   - `ENABLE_SARVAM_FALLBACKS`: `true`
   - `TAVILY_API_KEY`: `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`
   - `NEO4J_URI`: `neo4j+s://50580f6d.databases.neo4j.io`
   - `NEO4J_USER`: `50580f6d`
   - `NEO4J_PASSWORD`: `PUR0KsbQ26WeiRG5ta1557FSE16XwGRdolaFK3-2jBI`
   - `SUPABASE_URL`: `https://nsxxvhknsmrbsxqnqrop.supabase.co`
   - `SUPABASE_ANON_KEY`: *(from .env)*
   - `SUPABASE_SERVICE_ROLE_KEY`: *(from .env)*
   - `CORS_ORIGINS`: `*`
5. Click **Deploy**. Render gives you a public URL like `https://nagrik-backend.onrender.com`.

*(Alternatively, use `render.yaml` with Render Blueprints for 1-click deploy!)*

---

### 2. Deploy the Frontend (Vercel)
1. Go to [Vercel.com](https://vercel.com) and click **Add New...** -> **Project**.
2. Select the GitHub repo `Nagrik`.
3. Set **Root Directory** to `frontend`.
4. Under **Environment Variables**, add:
   ```env
   NEXT_PUBLIC_API_URL=https://nagrik-backend.onrender.com
   ```
5. Click **Deploy**. Vercel will build and deploy your site in ~60 seconds.

---

## Option 2: Single-Command Docker Compose (VPS / EC2 / Local Server)

If deploying to a Linux VPS (AWS EC2, DigitalOcean, Hetzner, GCP):

1. Clone the repo and navigate to it:
   ```bash
   git clone https://github.com/mrudduni/Nagrik.git
   cd Nagrik
   ```
2. Copy the `.env` template:
   ```bash
   cp nagrik-agent-backend/.env .env
   ```
3. Run with Docker Compose:
   ```bash
   docker-compose up -d --build
   ```
4. Access:
   - Frontend: `http://<your-server-ip>:3000`
   - Backend API Docs: `http://<your-server-ip>:8000/docs`

---

## Option 3: Railway (1-Click Container Deployment)
1. Create a new project on [Railway.app](https://railway.app).
2. Add a GitHub repository service pointing to `Nagrik`.
3. Add service 1 (`nagrik-agent-backend`) with port 8000.
4. Add service 2 (`frontend`) with port 3000 and set `NEXT_PUBLIC_API_URL` to the public backend domain.
