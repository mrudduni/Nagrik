"""
app/api/crawler.py
-------------------
REST endpoints for the Tavily scheme crawler feature.

Endpoints:
  POST /api/crawler/run              — trigger a crawl immediately (admin/cron)
  GET  /api/crawler/notifications    — get unread scheme notifications for a citizen
  POST /api/crawler/notifications/read  — mark notification(s) as read
  GET  /api/crawler/status           — get last crawl metadata
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/crawler")

# In-memory crawl state (replaced by Neo4j meta node in production)
_last_crawl: dict = {
    "status": "never_run",
    "started_at": None,
    "finished_at": None,
    "pages_crawled": 0,
    "schemes_extracted": 0,
    "schemes_ingested": 0,
    "notifications_sent": 0,
    "error": None,
}


# ── Pydantic models ─────────────────────────────────────────────────────────

class CrawlRunRequest(BaseModel):
    queries: Optional[list[str]] = None
    max_results_per_query: int = 5


class MarkReadRequest(BaseModel):
    citizen_id: str
    scheme_ids: list[str]  # empty list = mark ALL as read


# ── Background crawl task ────────────────────────────────────────────────────

def _run_crawl_task(queries: list[str] | None, max_results: int):
    """Full pipeline: Tavily → LLM extract → Neo4j ingest → citizen match."""
    global _last_crawl
    _last_crawl["status"] = "running"
    _last_crawl["started_at"] = datetime.now(timezone.utc).isoformat()
    _last_crawl["error"] = None

    try:
        from app.crawler.tavily_crawler import search_new_schemes
        from app.crawler.scheme_extractor import extract_schemes_from_pages
        from app.crawler.neo4j_ingestor import ingest_schemes
        from app.crawler.matcher import match_and_notify

        # Step 1: Crawl
        logger.info("🕷️ Tavily crawler: starting search…")
        pages = search_new_schemes(
            max_results_per_query=max_results,
            queries=queries,
        )
        _last_crawl["pages_crawled"] = len(pages)

        # Step 2: Extract structured data with Gemini
        logger.info(f"🤖 Extracting schemes from {len(pages)} pages…")
        extracted = extract_schemes_from_pages(pages)
        _last_crawl["schemes_extracted"] = len(extracted)

        # Step 3: Ingest new ones into Neo4j (deduped)
        logger.info(f"📥 Ingesting {len(extracted)} extracted schemes into Neo4j…")
        new_schemes = ingest_schemes(extracted)
        _last_crawl["schemes_ingested"] = len(new_schemes)

        # Step 4: Match to citizens & create notifications
        logger.info(f"🔔 Matching {len(new_schemes)} new schemes to citizens…")
        notifications = match_and_notify(new_schemes)
        _last_crawl["notifications_sent"] = len(notifications)

        _last_crawl["status"] = "completed"
        _last_crawl["finished_at"] = datetime.now(timezone.utc).isoformat()
        logger.info(
            f"✅ Crawl complete: {len(pages)} pages, {len(extracted)} extracted, "
            f"{len(new_schemes)} new, {len(notifications)} notifications."
        )

    except Exception as e:
        logger.error(f"❌ Crawl pipeline failed: {e}", exc_info=True)
        _last_crawl["status"] = "failed"
        _last_crawl["error"] = str(e)
        _last_crawl["finished_at"] = datetime.now(timezone.utc).isoformat()


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/run")
async def run_crawl(
    body: CrawlRunRequest,
    background_tasks: BackgroundTasks,
):
    """
    Trigger a scheme discovery crawl. Runs in the background.
    Safe to call from a GitHub Actions cron or cloud scheduler.
    """
    if _last_crawl["status"] == "running":
        return {"message": "A crawl is already running.", "status": "running"}

    background_tasks.add_task(
        _run_crawl_task,
        body.queries,
        body.max_results_per_query,
    )
    return {
        "message": "Crawl started in background.",
        "status": "started",
        "started_at": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/status")
async def crawl_status():
    """Get the status and statistics of the last crawl run."""
    return _last_crawl


@router.get("/notifications")
async def get_notifications(
    citizen_id: str = Query(..., description="Citizen ID to fetch notifications for"),
    unread_only: bool = Query(True, description="Return only unread notifications"),
    limit: int = Query(20),
):
    """
    Retrieve scheme notifications for a citizen.
    These are created by the crawler when a new scheme matches their interests.
    """
    from app.rag.neo4j_search import get_driver

    driver = get_driver()
    read_filter = "AND n.is_read = false" if unread_only else ""

    cypher = f"""
    MATCH (c:Citizen {{id: $citizen_id}})-[n:HAS_NOTIFICATION]->(s:Scheme)
    WHERE n.created_at IS NOT NULL {read_filter}
    RETURN
      s.id          AS scheme_id,
      s.name        AS scheme_name,
      s.summary     AS summary,
      s.source_url  AS source_url,
      n.message     AS message,
      n.created_at  AS created_at,
      n.is_read     AS is_read,
      n.match_reason AS match_reason
    ORDER BY n.created_at DESC
    LIMIT $limit
    """

    try:
        with driver.session() as sess:
            result = sess.run(cypher, citizen_id=citizen_id, limit=limit)
            rows = result.data()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Neo4j query failed: {e}")

    return {
        "citizen_id": citizen_id,
        "unread_count": len(rows),
        "notifications": [
            {
                "scheme_id": r["scheme_id"],
                "scheme_name": r["scheme_name"],
                "summary": (r["summary"] or "")[:200],
                "source_url": r["source_url"],
                "message": r["message"],
                "created_at": r["created_at"],
                "is_read": r["is_read"],
                "match_reason": r["match_reason"],
            }
            for r in rows
        ],
    }


@router.post("/notifications/read")
async def mark_notifications_read(body: MarkReadRequest):
    """
    Mark scheme notifications as read for a citizen.
    Pass empty scheme_ids list to mark ALL notifications as read.
    """
    from app.rag.neo4j_search import get_driver

    driver = get_driver()

    if body.scheme_ids:
        cypher = """
        MATCH (c:Citizen {id: $citizen_id})-[n:HAS_NOTIFICATION]->(s:Scheme)
        WHERE s.id IN $scheme_ids
        SET n.is_read = true, n.read_at = $now
        RETURN count(n) AS updated
        """
        params = {
            "citizen_id": body.citizen_id,
            "scheme_ids": body.scheme_ids,
            "now": datetime.now(timezone.utc).isoformat(),
        }
    else:
        cypher = """
        MATCH (c:Citizen {id: $citizen_id})-[n:HAS_NOTIFICATION]->(:Scheme)
        WHERE n.is_read = false
        SET n.is_read = true, n.read_at = $now
        RETURN count(n) AS updated
        """
        params = {
            "citizen_id": body.citizen_id,
            "now": datetime.now(timezone.utc).isoformat(),
        }

    try:
        with driver.session() as sess:
            result = sess.run(cypher, **params)
            row = result.single()
            updated = row["updated"] if row else 0
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Neo4j update failed: {e}")

    return {"marked_read": updated, "citizen_id": body.citizen_id}
