"""
Safely injects cancer videos from discovered_cancer_videos.json into fetch_youtube.py
by appending to CUSTOM_SEED_VIDEOS list. Strips newlines & cleans titles safely.
"""
import json

JSON_PATH = 'd:/verified-healthcare-content-reccomender/discovered_cancer_videos.json'
FETCH_PATH = 'd:/verified-healthcare-content-reccomender/backend/ingest/fetch_youtube.py'

with open(JSON_PATH, 'r', encoding='utf-8') as f:
    videos = json.load(f)

print(f"Loaded {len(videos)} cancer videos from JSON")

# Read current file
with open(FETCH_PATH, 'r', encoding='utf-8') as f:
    content = f.read()

# Try multiple possible end markers
END_MARKERS = [
    ']\n\n\ndef fetch_youtube_items',
    ']\n\ndef fetch_youtube_items',
    ']\n\n\nlogger',
    ']\n\nlogger',
]

idx = -1
used_marker = None
for marker in END_MARKERS:
    idx = content.find(marker)
    if idx != -1:
        used_marker = marker
        break

if idx == -1:
    # Show context around "def fetch_youtube_items"
    def_idx = content.find('def fetch_youtube_items')
    print(f"ERROR: Could not find known end marker. Context around def: {repr(content[max(0,def_idx-100):def_idx+20])}")
    exit(1)

print(f"Found end marker: {repr(used_marker)} at index {idx}")

# Build new entries as proper Python dict literals in the list
new_entries = ""
for v in videos:
    vid_id = str(v.get("id", "")).strip()
    title = str(v.get("title", "")).strip()
    channel = str(v.get("channel", "")).strip()
    vtype = str(v.get("type", "video")).strip()
    disease = str(v.get("disease", "cancer")).strip()

    # Escape any double quotes and remove newlines/special chars
    title = title.replace('\\', '\\\\').replace('"', "'").replace('\n', ' ').replace('\r', '').replace('\t', ' ')
    channel = channel.replace('\\', '\\\\').replace('"', "'").replace('\n', ' ').replace('\r', '')
    disease = disease.replace('"', "'").replace('\n', ' ').replace('\r', '')

    if not vid_id:
        continue

    new_entries += f'    {{"id": "{vid_id}", "title": "{title}", "channel": "{channel}", "type": "{vtype}", "disease": "{disease}"}},\n'

# Insert before the end marker
content = content[:idx] + new_entries + content[idx:]

with open(FETCH_PATH, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"Done. Injected {len(videos)} cancer video entries into fetch_youtube.py")
