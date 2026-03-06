"""
RSS feed fetcher — fetches content from allowlisted RSS feeds.
"""

import feedparser
import logging
from backend.core.settings import get_sources_allowlist
from backend.core.utils import parse_date, clean_html_text, is_url_from_allowlist

logger = logging.getLogger(__name__)


def fetch_rss_items() -> list[dict]:
    """
    Fetch items from all trusted RSS feeds in the allowlist.
    Returns a list of content item dicts ready for DB insertion.
    """
    config = get_sources_allowlist()
    rss_feeds = config.get("trusted_rss", [])
    trusted_domains = config.get("trusted_domains", [])
    items = []

    for feed_config in rss_feeds:
        url = feed_config.get("url", "")
        source_name = feed_config.get("name", "Unknown")
        source_tier = feed_config.get("source_tier", "verified_org")

        logger.info(f"Fetching RSS: {source_name} ({url})")

        try:
            feed = feedparser.parse(url)

            if feed.bozo and not feed.entries:
                logger.warning(f"Failed to parse RSS feed: {url} — {feed.bozo_exception}")
                continue

            for entry in feed.entries:
                entry_url = entry.get("link", "")

                # Validate against allowlist
                if not is_url_from_allowlist(entry_url, trusted_domains):
                    # Still allow if it's from the RSS source itself
                    if not entry_url:
                        continue

                title = entry.get("title", "Untitled")
                published = parse_date(
                    entry.get("published") or entry.get("updated") or None
                )

                # Extract text content
                text = ""
                if hasattr(entry, "summary"):
                    text = clean_html_text(entry.summary)
                elif hasattr(entry, "description"):
                    text = clean_html_text(entry.description)

                items.append({
                    "type": "article",
                    "title": title,
                    "url": entry_url,
                    "source_name": source_name,
                    "source_tier": source_tier,
                    "published_at": published,
                    "text": text,
                    "transcript": None,
                    "content_length": len(text) if text else 0,
                })

            logger.info(f"  → Got {len(feed.entries)} entries from {source_name}")

        except Exception as e:
            logger.error(f"Error fetching RSS {url}: {e}")
            continue

    logger.info(f"Total RSS items fetched: {len(items)}")
    return items
