import json

ORIGINAL_FETCH_YOUTUBE = '''"""
YouTube fetcher — fetches video metadata and transcripts from
allowlisted YouTube channels.
"""

import logging
from backend.core.settings import get_sources_allowlist

logger = logging.getLogger(__name__)


def fetch_youtube_items() -> list[dict]:
    """
    Fetch video items from trusted YouTube channels.
    Uses youtube-transcript-api for transcripts when available.

    Note: For a full implementation, you'd use the YouTube Data API
    to list videos from channels. This baseline version uses a
    curated list of known video IDs from trusted channels.
    """
    config = get_sources_allowlist()
    channels = config.get("trusted_youtube_channels", [])
    items = []

    import yt_dlp

    ydl_opts = {
        'extract_flat': True,
        'quiet': True,
        'playlistend': 10 # Scrape up to 10 latest videos from the main channel feed
    }

    # Fetch static custom items first
    logger.info("Fetching custom static videos (Common Diseases)...")
    for v in CUSTOM_SEED_VIDEOS:
        vid_id = v["id"]
        title = v["title"]
        source_name = v["channel"]
        expected_type = v["type"]
        
        url = f"https://www.youtube.com/watch?v={vid_id}"
        transcript_text = _get_transcript(vid_id)
        
        items.append({
            "type": expected_type,
            "title": title,
            "url": url,
            "source_name": source_name,
            "source_tier": "verified_org",
            "published_at": None,
            "text": None,
            "transcript": transcript_text,
            "content_length": len(transcript_text) if transcript_text else 0,
        })
        logger.info(f"  → Static {expected_type.capitalize()}: {title[:30]}... (transcript: {'yes' if transcript_text else 'no'})")

    for channel in channels:
        channel_id = channel.get("channel_id")
        source_name = channel.get("name")
        source_tier = channel.get("source_tier")
        
        if not channel_id:
             continue
             
        # Scrape both videos and shorts explicitly
        targets = [
            (f"https://www.youtube.com/channel/{channel_id}/videos", "video", {'youtube': {'tab': ['videos']}}),
            (f"https://www.youtube.com/channel/{channel_id}/shorts", "short_video", {'youtube': {'tab': ['shorts']}})
        ]
        
        for base_url, expected_type, extractor_args in targets:
            try:
                # Update ydl_opts for each target to ensure correct tab is pulled
                opts = ydl_opts.copy()
                opts['extractor_args'] = extractor_args
                
                with yt_dlp.YoutubeDL(opts) as ydl:
                    logger.info(f"Scraping {base_url}...")
                    info = ydl.extract_info(base_url, download=False)
                    if not info or 'entries' not in info:
                        continue
                        
                    for entry in info['entries']:
                        if not entry:
                            continue
                            
                        vid_id = entry.get("id")
                        title = entry.get("title", "Unknown Title")
                        
                        url = f"https://www.youtube.com/watch?v={vid_id}"
                        
                        # Get Transcript
                        transcript_text = _get_transcript(vid_id)
                        
                        items.append({
                            "type": expected_type,
                            "title": title,
                            "url": url,
                            "source_name": source_name,
                            "source_tier": source_tier,
                            "published_at": None,
                            "text": None,
                            "transcript": transcript_text,
                            "content_length": len(transcript_text) if transcript_text else 0,
                        })
                        logger.info(f"  → {expected_type.capitalize()}: {title} (transcript: {'yes' if transcript_text else 'no'})")
            except Exception as e:
                logger.error(f"Error scraping {base_url}: {e}")

    logger.info(f"Total YouTube items fetched dynamically: {len(items)}")
    return items


def _get_transcript(video_id: str) -> str | None:
    """Attempt to fetch transcript for a YouTube video."""
    try:
        from youtube_transcript_api import YouTubeTranscriptApi

        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        text = " ".join(segment["text"] for segment in transcript_list)
        return text
    except Exception as e:
        logger.warning(f"Could not fetch transcript for {video_id}: {e}")
        return None
'''

with open('d:/verified-healthcare-content-reccomender/discovered_videos.json', 'r', encoding='utf-8') as f:
    custom_videos = json.load(f)

# Convert to python code string
list_str = "CUSTOM_SEED_VIDEOS = [\n"
for v in custom_videos:
    id_str = v.get("id")
    title_str = v.get("title", "").replace('"', "'").replace('\\', '')
    channel_str = v.get("channel", "").replace('"', "'")
    type_str = v.get("type", "video")
    disease = v.get("disease", "")
    list_str += f'    {{"id": "{id_str}", "title": "{title_str}", "channel": "{channel_str}", "type": "{type_str}", "disease": "{disease}"}},\n'
list_str += "]\n\n"

content = list_str + ORIGINAL_FETCH_YOUTUBE

with open('d:/verified-healthcare-content-reccomender/backend/ingest/fetch_youtube.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Restored and updated fetch_youtube.py successfully.")
