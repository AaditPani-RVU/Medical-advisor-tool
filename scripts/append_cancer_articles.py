import json

with open('d:/verified-healthcare-content-reccomender/data/raw_ingest/discovered_cancer_articles.json', 'r', encoding='utf-8') as f:
    new_urls = json.load(f)

with open('d:/verified-healthcare-content-reccomender/backend/ingest/fetch_web.py', 'r', encoding='utf-8') as f:
    content = f.read()

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

with open('d:/verified-healthcare-content-reccomender/backend/ingest/fetch_web.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Appended cancer articles to fetch_web.py")
