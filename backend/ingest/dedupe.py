"""
Deduplication module — prevents duplicate content items in the DB.
"""

import logging
from backend.core.db import get_db

logger = logging.getLogger(__name__)


def dedupe_items(items: list[dict]) -> list[dict]:
    """
    Remove items whose URLs already exist in the database.
    Also dedupes within the input list itself.
    """
    if not items:
        return []

    # Get existing URLs from DB
    existing_urls = set()
    with get_db() as conn:
        cursor = conn.execute("SELECT url FROM content_items")
        for row in cursor.fetchall():
            existing_urls.add(row["url"])

    # Dedupe
    seen_urls = set()
    unique_items = []

    for item in items:
        url = item.get("url", "")
        if not url:
            continue
        if url in existing_urls:
            logger.debug(f"  Skip (exists in DB): {url}")
            continue
        if url in seen_urls:
            logger.debug(f"  Skip (duplicate in batch): {url}")
            continue

        seen_urls.add(url)
        unique_items.append(item)

    skipped = len(items) - len(unique_items)
    if skipped > 0:
        logger.info(f"  Deduped: {skipped} duplicates removed, {len(unique_items)} new items")

    return unique_items
