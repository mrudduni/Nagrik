"""
scripts/run_crawler_now.py
--------------------------
Manual CLI runner for the Tavily Scheme Crawler.
Executes the full pipeline:
  1. Search official Indian government domains via Tavily
  2. Extract structured scheme data with Gemini LLM
  3. Ingest newly discovered schemes into Neo4j
  4. Match schemes to citizen interest profiles and create notifications

Usage:
  python scripts/run_crawler_now.py
  python scripts/run_crawler_now.py --max-results 3
"""
from __future__ import annotations

import argparse
import logging
import os
import sys

# Add backend directory to sys.path so app modules import cleanly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "nagrik-agent-backend")))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("crawler_runner")


def main():
    parser = argparse.ArgumentParser(description="Run Tavily Scheme Crawler")
    parser.add_argument("--max-results", type=int, default=3, help="Max results per search query")
    parser.add_argument("--query", type=str, default=None, help="Optional custom search query")
    args = parser.parse_args()

    queries = [args.query] if args.query else None

    logger.info("==================================================")
    logger.info("   NAGRIK TAVILY SCHEME CRAWLER & INGESTOR       ")
    logger.info("==================================================")

    from app.config import settings
    if not settings.tavily_api_key:
        logger.error("❌ TAVILY_API_KEY is not configured in .env!")
        logger.info("Please set TAVILY_API_KEY in nagrik-agent-backend/.env or your environment.")
        return

    from app.api.crawler import _run_crawl_task, _last_crawl
    _run_crawl_task(queries=queries, max_results=args.max_results)

    logger.info("--------------------------------------------------")
    logger.info(f"Status:             {_last_crawl['status']}")
    logger.info(f"Pages crawled:      {_last_crawl['pages_crawled']}")
    logger.info(f"Schemes extracted:  {_last_crawl['schemes_extracted']}")
    logger.info(f"Schemes ingested:   {_last_crawl['schemes_ingested']}")
    logger.info(f"Notifications sent: {_last_crawl['notifications_sent']}")
    if _last_crawl.get("error"):
        logger.error(f"Error encountered:  {_last_crawl['error']}")
    logger.info("==================================================")


if __name__ == "__main__":
    main()
