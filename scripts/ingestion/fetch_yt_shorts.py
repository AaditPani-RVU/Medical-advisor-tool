import os
import json
import subprocess
import json

CHANNELS = {
    "@mayoclinic": ("Mayo Clinic", "verified_org"),
    "@ClevelandClinic": ("Cleveland Clinic", "verified_org"),
    "@WHO": ("World Health Organization", "verified_org"),
    "@DoctorMike": ("Doctor Mike", "verified_creator"),
    "@drmarkhyman": ("Dr. Mark Hyman", "verified_creator"),
}

IRRELEVANT_KEYWORDS = ["celebrat", "giveaway", "win", "happy", "promo", "live", "q&a", "podcast"]

def fetch_shorts(handle, name, tier):
    print(f"Fetching shorts for {handle}...")
    url = f"https://www.youtube.com/{handle}/shorts"
    cmd = ["yt-dlp", url, "--dump-json", "--playlist-end", "15"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    reels = []
    for line in result.stdout.strip().split("\n"):
        if not line: continue
        try:
            data = json.loads(line)
            title = data.get("title", "")
            if not title: continue
            
            # Check irrelevance
            title_lower = title.lower()
            if any(k in title_lower for k in IRRELEVANT_KEYWORDS):
                continue
                
            short_url = f"https://www.youtube.com/shorts/{data.get('id')}"
            
            reels.append({
                "type": "instagram_reel",
                "title": title,
                "url": short_url,
                "source_name": name,
                "source_tier": tier,
                "published_at": "2026-03-05T10:00:00Z",
                "tags": ["education"],
                "summary": {
                    "summary": title,
                    "key_points": ["Educational short detailing facts about this condition."],
                    "warnings": []
                }
            })
        except BaseException as e:
            print(f"Error parsing json line: {e}")
    return reels

all_reels = []
for handle, (name, tier) in CHANNELS.items():
    all_reels.extend(fetch_shorts(handle, name, tier))
    
with open("generated_mock_reels.py", "w", encoding="utf-8") as f:
    f.write("NEW_REELS = [\n")
    for r in all_reels:
        f.write(f"    {repr(r)},\n")
    f.write("]\n")

print(f"Generated {len(all_reels)} reels!")
