"""
Utility helpers — URL validation, domain extraction, date parsing.
"""

import re
from urllib.parse import urlparse
from datetime import datetime


def extract_domain(url: str) -> str:
    """Extract the domain from a URL (e.g., 'www.cdc.gov' -> 'cdc.gov')."""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        # Remove www. prefix
        if domain.startswith("www."):
            domain = domain[4:]
        return domain
    except Exception:
        return ""


def is_url_from_allowlist(url: str, trusted_domains: list[str]) -> bool:
    """Check if a URL's domain is in the trusted domains list."""
    domain = extract_domain(url)
    if not domain:
        return False
    for trusted in trusted_domains:
        if domain == trusted or domain.endswith("." + trusted):
            return True
    return False


def parse_date(date_str: str | None) -> str | None:
    """
    Attempt to parse a date string into ISO format.
    Returns None if parsing fails.
    """
    if not date_str:
        return None

    formats = [
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d",
        "%a, %d %b %Y %H:%M:%S %z",
        "%a, %d %b %Y %H:%M:%S %Z",
        "%d %b %Y",
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str.strip(), fmt)
            return dt.isoformat()
        except ValueError:
            continue
    return date_str


def truncate_text(text: str, max_length: int = 3000) -> str:
    """Truncate text to max_length characters for LLM input."""
    if not text:
        return ""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."


def clean_html_text(text: str) -> str:
    """Remove extra whitespace and clean up extracted text."""
    if not text:
        return ""
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def get_source_tier_badge(source_tier: str) -> str:
    """Return a display badge for the source tier."""
    badges = {
        "verified_org": "✅ Verified Organization",
        "verified_creator": "🔵 Verified Creator",
    }
    return badges.get(source_tier, "⚪ Source")
