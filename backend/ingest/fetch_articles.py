import logging
import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from backend.core.settings import get_sources_allowlist

logger = logging.getLogger(__name__)

def fetch_rss_articles() -> list[dict]:
    """
    Fetch articles from trusted RSS feeds.
    Downloads the URL and extracts text via BeautifulSoup.
    """
    config = get_sources_allowlist()
    rss_feeds = config.get("trusted_rss", [])
    items = []

    for feed in rss_feeds:
        feed_url = feed.get("url")
        source_name = feed.get("name")
        source_tier = feed.get("source_tier", "verified_org")
        
        if not feed_url:
            continue
            
        logger.info(f"Parsing RSS feed: {source_name} ({feed_url})")
        
        try:
            parsed = feedparser.parse(feed_url)
            
            # Limit to 5 most recent articles per feed for speed
            entries = parsed.entries[:5]
            
            for entry in entries:
                # Basic metadata extraction
                title = entry.get("title", "Unknown Title")
                link = entry.get("link", "")
                
                # Fetch full text
                full_text = _extract_article_text(link)
                
                if not full_text or len(full_text) < 150:
                    logger.warning(f"  → Skipping {title} (too short or unreachable).")
                    continue
                    
                items.append({
                    "type": "article",
                    "title": title,
                    "url": link,
                    "source_name": source_name,
                    "source_tier": source_tier,
                    "published_at": None, # Will be set by DB default if missing
                    "text": full_text,
                    "transcript": None,
                    "content_length": len(full_text),
                })
                logger.info(f"  → Article: {title} ({len(full_text)} chars)")
                
        except Exception as e:
            logger.error(f"Error processing feed {source_name} : {e}")
            
    logger.info(f"Total Article items fetched: {len(items)}")
    return items

def _extract_article_text(url: str) -> str | None:
    """Download an article and extract main text paragraph by paragraph."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        
        soup = BeautifulSoup(resp.content, "html.parser")
        
        # Remove nav, header, footer, script, style tags
        for element in soup(["nav", "header", "footer", "script", "style", "aside"]):
            element.decompose()
            
        paragraphs = soup.find_all("p")
        text_blocks = [p.get_text(separator=' ', strip=True) for p in paragraphs]
        
        # Join long enough paragraphs
        clean_text = " ".join([b for b in text_blocks if len(b) > 30])
        return clean_text
    except Exception as e:
        logger.debug(f"Failed to extract {url}: {e}")
        return None
