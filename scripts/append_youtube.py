import json

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

with open('d:/verified-healthcare-content-reccomender/backend/ingest/fetch_youtube.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Insert the STATIC list before the function definition
insert_idx = content.find('def fetch_youtube_items')
content = content[:insert_idx] + list_str + content[insert_idx:]

static_logic_str = """
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

"""

insert_idx_2 = content.find('logger.info(f"Total YouTube items fetched dynamically')
content = content[:insert_idx_2] + static_logic_str + content[insert_idx_2:]

with open('d:/verified-healthcare-content-reccomender/backend/ingest/fetch_youtube.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Appended 129 static YouTube videos and updated fetch logic.")
