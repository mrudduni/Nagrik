"""
app/crawler/scheduler.py
------------------------
Background periodic scheduler that runs the Tavily scheme crawler every 24 hours
(configurable via CRAWLER_INTERVAL_HOURS or settings).

Can be started/stopped during FastAPI application startup/shutdown.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

logger = logging.getLogger(__name__)

_scheduler_task: Optional[asyncio.Task] = None
_stop_event: asyncio.Event = asyncio.Event()

# Default crawl interval in hours
DEFAULT_INTERVAL_HOURS = 24


async def _periodic_crawler_worker(interval_seconds: int):
    """Loop that wakes up every `interval_seconds` and triggers a crawl."""
    from app.api.crawler import _run_crawl_task, _last_crawl

    logger.info(
        f"⏰ Tavily 24-hour crawler scheduler active. Interval: {interval_seconds / 3600:.1f} hours."
    )

    # Initial delay: wait 30 seconds after server boot before the first check
    # so the app starts up swiftly and finishes initializing Neo4j/LLM drivers
    try:
        await asyncio.wait_for(_stop_event.wait(), timeout=30.0)
        return  # Stopped during initial delay
    except asyncio.TimeoutError:
        pass

    while not _stop_event.is_set():
        try:
            from app.config import settings
            if not settings.tavily_api_key:
                logger.info("ℹ️ Tavily crawler scheduler: TAVILY_API_KEY not set yet. Skipping cycle until configured.")
            else:
                logger.info("⏰ Scheduler triggering periodic Tavily scheme crawl...")
                # Run the crawl in a threadpool executor so it doesn't block the async event loop
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(None, _run_crawl_task, None, 5)
                logger.info("⏰ Periodic Tavily scheme crawl finished successfully.")
        except Exception as e:
            logger.error(f"❌ Error during scheduled Tavily crawl: {e}", exc_info=True)

        try:
            # Wait for next interval or until stop_event is set
            await asyncio.wait_for(_stop_event.wait(), timeout=interval_seconds)
            break
        except asyncio.TimeoutError:
            continue


def start_crawler_scheduler(interval_hours: float = DEFAULT_INTERVAL_HOURS):
    """Start the periodic crawler background task."""
    global _scheduler_task, _stop_event

    if _scheduler_task and not _scheduler_task.done():
        logger.warning("Crawler scheduler is already running.")
        return

    _stop_event.clear()
    interval_seconds = int(interval_hours * 3600)
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.get_event_loop()
    _scheduler_task = loop.create_task(
        _periodic_crawler_worker(interval_seconds),
        name="tavily_24h_crawler",
    )
    logger.info(f"🚀 Crawler scheduler scheduled to run every {interval_hours} hours.")


def stop_crawler_scheduler():
    """Signal the crawler scheduler to gracefully stop."""
    global _scheduler_task, _stop_event
    _stop_event.set()
    if _scheduler_task and not _scheduler_task.done():
        _scheduler_task.cancel()
        logger.info("🛑 Crawler scheduler stopped.")
