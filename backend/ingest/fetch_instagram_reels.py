"""
Instagram Reels Fetcher — retrieves public reel metadata from allowlisted
healthcare creators using instaloader.

Only ingests reels from accounts listed in configs/instagram_allowlist.yaml.
No arbitrary scraping. Gracefully skips if instaloader is not available.
"""

import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


def _load_allowlist() -> list[dict]:
    """Load the trusted Instagram accounts from the YAML config."""
    from backend.core.settings import load_yaml_config

    config = load_yaml_config("instagram_allowlist.yaml")
    accounts = config.get("trusted_instagram_accounts", [])
    if not accounts:
        logger.warning("Instagram allowlist is empty — nothing to fetch")
    return accounts


def _fetch_reels_for_account(handle: str, name: str, trust_tier: str,
                              max_reels: int = 5) -> list[dict]:
    """
    Fetch the latest public reels for a single Instagram account.
    Returns a list of content item dicts ready for insertion.
    """
    try:
        import instaloader
    except ImportError:
        logger.warning("instaloader not installed — pip install instaloader")
        return []

    items = []
    loader = instaloader.Instaloader(
        download_pictures=False,
        download_videos=False,
        download_video_thumbnails=False,
        download_geotags=False,
        download_comments=False,
        save_metadata=False,
        compress_json=False,
        quiet=True,
    )

    from backend.core.settings import settings
    if settings.instagram_username and settings.instagram_password:
        try:
            logger.info(f"Logging into Instagram as {settings.instagram_username}...")
            loader.login(settings.instagram_username, settings.instagram_password)
        except Exception as e:
            logger.warning(f"Failed to login to Instagram with provided credentials: {e}")

    try:
        profile = instaloader.Profile.from_username(loader.context, handle)
    except Exception as e:
        logger.warning(f"  Could not load Instagram profile @{handle}: {e}")
        return []

    count = 0
    try:
        for post in profile.get_posts():
            # Only process reels (is_video posts that are "reels" type)
            if not post.is_video:
                continue

            reel_url = f"https://www.instagram.com/reel/{post.shortcode}/"
            caption = (post.caption or "").strip()
            title = caption[:120] + "…" if len(caption) > 120 else caption
            if not title:
                title = f"Reel by @{handle}"

            published_at = post.date_utc.isoformat() + "Z" if post.date_utc else None

            items.append({
                "type": "instagram_reel",
                "title": title,
                "url": reel_url,
                "source_name": name,
                "source_tier": trust_tier,
                "published_at": published_at,
                "text": caption,  # caption as text for summarization
                "transcript": None,
                "content_length": len(caption) if caption else 0,
            })

            count += 1
            if count >= max_reels:
                break

    except Exception as e:
        logger.warning(f"  Error fetching posts for @{handle}: {e}")

    return items


def fetch_instagram_reels(max_reels_per_account: int = 5) -> list[dict]:
    """
    Main entry point — fetch reels from all allowlisted Instagram creators.

    Args:
        max_reels_per_account: Maximum number of reels to fetch per account.

    Returns:
        List of content item dicts ready for deduplication and insertion.
    """
    try:
        import instaloader  # noqa: F401
    except ImportError:
        logger.warning(
            "instaloader is not installed. Skipping Instagram ingestion. "
            "Install with: pip install instaloader"
        )
        return []

    accounts = _load_allowlist()
    if not accounts:
        return []

    all_items = []
    logger.info(f"Fetching reels from {len(accounts)} allowlisted Instagram accounts...")

    for account in accounts:
        handle = account.get("handle", "")
        name = account.get("name", handle)
        trust_tier = account.get("trust_tier", "verified_creator")

        logger.info(f"  Fetching reels from @{handle} ({name})...")

        items = _fetch_reels_for_account(
            handle=handle,
            name=name,
            trust_tier=trust_tier,
            max_reels=max_reels_per_account,
        )

        logger.info(f"    Found {len(items)} reels from @{handle}")
        all_items.extend(items)

    logger.info(f"Total Instagram reels fetched: {len(all_items)}")
    return all_items
