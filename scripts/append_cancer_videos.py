import json

with open('d:/verified-healthcare-content-reccomender/data/raw_ingest/discovered_cancer_videos.json', 'r', encoding='utf-8') as f:
    custom_videos = json.load(f)

list_str = ""
for v in custom_videos:
    id_str = v.get("id")
    title_str = v.get("title", "").replace('"', "'").replace('\\', '')
    channel_str = v.get("channel", "").replace('"', "'")
    type_str = v.get("type", "video")
    disease = v.get("disease", "cancer")
    list_str += f'    {{"id": "{id_str}", "title": "{title_str}", "channel": "{channel_str}", "type": "{type_str}", "disease": "{disease}"}},\n'

with open('d:/verified-healthcare-content-reccomender/backend/ingest/fetch_youtube.py', 'r', encoding='utf-8') as f:
    content = f.read()

insert_idx = content.find(']\n\n\ndef fetch_youtube_items')
content = content[:insert_idx] + list_str + content[insert_idx:]

with open('d:/verified-healthcare-content-reccomender/backend/ingest/fetch_youtube.py', 'w', encoding='utf-8') as f:
    f.write(content)

print(f"Appended {len(custom_videos)} cancer videos to fetch_youtube.py")
