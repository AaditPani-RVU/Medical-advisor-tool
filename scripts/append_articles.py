import json

with open('d:/verified-healthcare-content-reccomender/discovered_articles.json', 'r') as f:
    new_urls = json.load(f)

with open('d:/verified-healthcare-content-reccomender/backend/ingest/fetch_web.py', 'r') as f:
    content = f.read()

# find end of DEFAULT_SEED_URLS list in file
# which is marked by "]\n\n\ndef fetch_web_pages("
insert_idx = content.find(']\n\n\ndef fetch_web_pages(')

new_str = ""
for item in new_urls:
    new_str += f"""    {{
        "url": "{item['url']}",
        "source_name": "{item['source_name']}",
        "source_tier": "{item['source_tier']}",
    }},
"""

content = content[:insert_idx] + new_str + content[insert_idx:]

with open('d:/verified-healthcare-content-reccomender/backend/ingest/fetch_web.py', 'w') as f:
    f.write(content)

print("Appended 76 new articles to fetch_web.py")
