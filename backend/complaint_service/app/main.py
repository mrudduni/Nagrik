"""
Nagrik Complaint Service — FastAPI Application Entry Point
"""
from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.services.embedder import EmbeddingService
from app.config import settings

logger = logging.getLogger(__name__)

# Global embedding service instance
_embedding_service: EmbeddingService | None = None


def get_embedding_service() -> EmbeddingService:
    """Get the global embedding service instance."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService(
            model_name=settings.EMBEDDING_MODEL,
            index_path=settings.FAISS_INDEX_PATH,
        )
    return _embedding_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle."""
    # --- Startup ---
    logger.info("Initializing database...")
    try:
        await init_db()
    except Exception as e:
        logger.warning(f"Database init warning: {e}")

    logger.info("Loading FAISS index...")
    svc = get_embedding_service()
    svc.load_index()

    # Start SLA Monitor background job (optional, requires APScheduler)
    try:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        from app.services.sla_monitor import SLAMonitor
        from app.database import async_session_maker

        scheduler = AsyncIOScheduler()

        async def _sla_check_job():
            async with async_session_maker() as session:
                monitor = SLAMonitor()
                escalated = await monitor.check_sla_compliance(session)
                if escalated:
                    logger.info(f"SLA check escalated {len(escalated)} complaints")

        scheduler.add_job(
            _sla_check_job,
            "interval",
            minutes=settings.SLA_CHECK_INTERVAL_MINUTES,
        )
        scheduler.start()
        logger.info(f"SLA monitor started (interval={settings.SLA_CHECK_INTERVAL_MINUTES}min)")
        app.state.scheduler = scheduler
    except ImportError:
        logger.warning("APScheduler not installed — SLA background monitor disabled")
    except Exception as exc:
        logger.warning(f"Failed to start SLA scheduler: {exc}")

    yield

    # --- Shutdown ---
    if hasattr(app.state, "scheduler"):
        app.state.scheduler.shutdown(wait=False)
    svc = get_embedding_service()
    svc.save_index()
    logger.info("Complaint service shut down cleanly.")


app = FastAPI(
    title="Nagrik Complaint Service",
    description=(
        "Backend micro-service for citizen complaint submission, classification, "
        "duplicate detection, priority scoring, department routing, SLA monitoring, "
        "escalation, and resolution verification."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow all origins during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Mount Routers (both /api/v1 and root for maximum client compatibility) ---
from app.api.complaints import router as complaints_router  # noqa: E402
from app.api.clusters import router as clusters_router  # noqa: E402
from app.api.analytics import router as analytics_router  # noqa: E402
from app.api.admin import router as admin_router  # noqa: E402

# Versioned API routes
app.include_router(complaints_router, prefix="/api/v1")
app.include_router(clusters_router, prefix="/api/v1")
app.include_router(analytics_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")

# Direct routes (supports Navya's person3_client: http://localhost:8002/complaints)
app.include_router(complaints_router)
app.include_router(clusters_router)
app.include_router(analytics_router)
app.include_router(admin_router)


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "service": "nagrik-complaint-service", "version": "1.0.0"}
