"""
Video-only ingestion runner — fetches YouTube videos, dedupes,
inserts into DB, and runs LLM summarization on videos only.

Usage:
    python -m backend.ingest.ingest_videos
"""

import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.core.db import get_db
from backend.core.settings import DATA_DIR
from backend.ingest.fetch_youtube import fetch_youtube_items
from backend.ingest.dedupe import dedupe_items

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def insert_video_items(items: list[dict]) -> int:
    """Insert video items into the database. Returns count inserted."""
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


def run_llm_on_videos():
    """Run LLM summarization and tagging on unsummarized video items."""
    try:
        from backend.llm.summarizer import summarize_content
        from backend.llm.tagger import tag_content
        from backend.core.db import get_db, execute_query
        import json

        rows = execute_query(
            "SELECT id, title, text, transcript FROM content_items "
            "WHERE type = 'video' AND summary_json = '{}'"
        )

        if not rows:
            logger.info("  No unsummarized videos found.")
            return

        logger.info(f"  Processing {len(rows)} videos...")
        for row in rows:
            item_id = row["id"]
            title = row["title"] or ""
            text = row["transcript"] or row["text"] or title

            logger.info(f"  → Summarizing: {title[:60]}...")
            summary = summarize_content(title, "YouTube", text)

            logger.info(f"  → Tagging: {title[:60]}...")
            tags = tag_content(title, text)

            with get_db() as conn:
                conn.execute(
                    "UPDATE content_items SET summary_json = ?, tags_json = ? WHERE id = ?",
                    (json.dumps(summary), json.dumps(tags), item_id),
                )
            logger.info(f"    ✓ Done (tags: {tags})")

    except Exception as e:
        logger.warning(f"LLM processing skipped: {e}")


def run_video_ingestion():
    """Video-only ingestion pipeline."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    logger.info("=" * 50)
    logger.info("Video-only ingestion pipeline")
    logger.info("=" * 50)

    # 1. Fetch YouTube videos
    logger.info("\n── Fetching YouTube videos ──")
    try:
        yt_items = fetch_youtube_items()
    except Exception as e:
        logger.error(f"YouTube fetch failed: {e}")
        return

    logger.info(f"Fetched {len(yt_items)} videos")

    # 2. Dedupe against existing DB
    logger.info("\n── Deduplicating ──")
    unique_items = dedupe_items(yt_items)
    logger.info(f"  {len(unique_items)} new videos after dedup")

    # 3. Insert
    logger.info("\n── Inserting into database ──")
    inserted = insert_video_items(unique_items)
    logger.info(f"  Inserted {inserted} new videos")

    # 4. LLM processing
    logger.info("\n── LLM processing (videos only) ──")
    run_llm_on_videos()

    logger.info("\n" + "=" * 50)
    logger.info(f"Done! {inserted} videos added.")
    logger.info("=" * 50)


if __name__ == "__main__":
    run_video_ingestion()
