import json, os

fpath = 'd:/verified-healthcare-content-reccomender/discovered_cancer_videos.json'
if not os.path.exists(fpath):
    print("File NOT found:", fpath)
else:
    with open(fpath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"Total discovered cancer videos: {len(data)}")
    for v in data[:10]:
        print(f"  [{v.get('disease')}] {v.get('id')} - {v.get('title','')[:60]}")
