"""
Ingestion orchestrator — runs all fetchers, dedupes, inserts into DB,
and triggers LLM summarization.
"""

import json
import logging
import sys
from pathlib import Path

# Add project root to path for direct script execution
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.core.db import get_db
from backend.core.settings import DATA_DIR
from backend.ingest.fetch_articles import fetch_rss_articles
from backend.ingest.fetch_web import fetch_web_pages
from backend.ingest.fetch_youtube import fetch_youtube_items
from backend.ingest.dedupe import dedupe_items

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def insert_items(items: list[dict]) -> int:
    """Insert content items into the database. Returns count inserted."""
    if not items:
        return 0

    inserted = 0
    with get_db() as conn:
        for item in items:
            try:
                conn.execute(
                    """
                    INSERT INTO content_items
                        (type, title, url, source_name, source_tier,
                         published_at, text, transcript, tags_json,
                         summary_json, content_length)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, '[]', '{}', ?)
                    """,
                    (
                        item["type"],
                        item["title"],
                        item["url"],
                        item["source_name"],
                        item["source_tier"],
                        item.get("published_at"),
                        item.get("text"),
                        item.get("transcript"),
                        item.get("content_length", 0),
                    ),
                )
                inserted += 1
            except Exception as e:
                logger.error(f"  Error inserting {item.get('url')}: {e}")

    return inserted


def run_llm_processing():
    """
    Run LLM summarization and tagging on items that don't have summaries yet.
    Gracefully skips if Ollama is not available.
    """
    try:
        from backend.llm.summarizer import summarize_unsummarized_items
        from backend.llm.tagger import tag_untagged_items

        logger.info("Running LLM summarization...")
        summarize_unsummarized_items()

        logger.info("Running LLM tagging...")
        tag_untagged_items()

    except Exception as e:
        logger.warning(
            f"LLM processing skipped (Ollama may not be running): {e}"
        )
        logger.info("Items were ingested without LLM summaries. "
                     "Run again with Ollama available to generate summaries.")


def run_ingestion():
    """Main ingestion pipeline."""
    # Ensure data directories exist
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "cache").mkdir(exist_ok=True)
    (DATA_DIR / "raw_ingest").mkdir(exist_ok=True)

    logger.info("=" * 60)
    logger.info("Starting content ingestion pipeline")
    logger.info("=" * 60)

    all_items = []

    # 1. Fetch from RSS feeds
    logger.info("\n── Fetching RSS feeds ──")
    try:
        rss_items = fetch_rss_articles()
        all_items.extend(rss_items)
    except Exception as e:
        logger.error(f"RSS fetch failed: {e}")

    # 2. Fetch from web pages
    logger.info("\n── Fetching web pages ──")
    try:
        web_items = fetch_web_pages()
        all_items.extend(web_items)
    except Exception as e:
        logger.error(f"Web fetch failed: {e}")

    # 3. Fetch from YouTube
    logger.info("\n── Fetching YouTube videos ──")
    try:
        yt_items = fetch_youtube_items()
        all_items.extend(yt_items)
    except Exception as e:
        logger.error(f"YouTube fetch failed: {e}")

    # 4. Fetch from Instagram Reels
    logger.info("\n── Fetching Instagram Reels ──")
    try:
        from backend.ingest.fetch_instagram_reels import fetch_instagram_reels
        ig_items = fetch_instagram_reels()
        all_items.extend(ig_items)
    except Exception as e:
        logger.error(f"Instagram fetch failed: {e}")

    logger.info(f"\nTotal items fetched: {len(all_items)}")

    # 4. Deduplicate
    logger.info("\n── Deduplicating ──")
    unique_items = dedupe_items(all_items)

    # 5. Insert into DB
    logger.info("\n── Inserting into database ──")
    inserted = insert_items(unique_items)
    logger.info(f"  Inserted {inserted} new items into database")

    # 6. Run LLM processing
    logger.info("\n── LLM processing ──")
    run_llm_processing()

    logger.info("\n" + "=" * 60)
    logger.info("Ingestion pipeline complete!")
    logger.info("=" * 60)


if __name__ == "__main__":
    run_ingestion()
