import subprocess
import json
import time

diseases = [
    "diabetes", "cold", "flu", "asthma", "hypertension", 
    "arthritis", "depression", "anxiety", "migraine", "back pain",
    "allergies", "heart disease", "obesity", "cancer"
]

channels = [
    "Mayo Clinic", "Cleveland Clinic", "NHS", "Johns Hopkins Medicine"
] # highly trusted, patient-facing

results = []

print("Starting discovery...")

for disease in diseases:
    for channel in channels:
        query = f"{disease} {channel}"
        print(f"Searching: {query}")
        
        # We try to get 2 normal videos and 2 shorts (if possible). 
        # yt-dlp "ytsearch3:query" --dump-json
        try:
            cmd = [
                "yt-dlp",
                f"ytsearch3:{query}",
                "--dump-json",
                "--lazy-playlist",
                "--no-warnings"
            ]
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, stderr = process.communicate()
            
            for line in stdout.splitlines():
                if not line.strip(): continue
                data = json.loads(line)
                vid_id = data.get("id")
                title = data.get("title")
                uploader = data.get("uploader")
                duration = data.get("duration", 0)
                
                # Check if it actually matches our target channel roughly to avoid weird results
                if channel.lower() not in uploader.lower():
                    # NHS might be "NHS" or "National Health Service"
                    if channel == "NHS" and "nhs" not in uploader.lower() and "national health service" not in uploader.lower():
                        continue
                    if channel != "NHS":
                        continue
                
                v_type = "short_video" if duration and duration <= 60 else "video"
                
                results.append({
                    "id": vid_id,
                    "title": title,
                    "channel": channel,
                    "type": v_type,
                    "disease": disease
                })
        except Exception as e:
            print(f"Error on {query}: {e}")
            
        time.sleep(1) # be nice

print(f"Discovered {len(results)} videos.")
with open("d:/verified-healthcare-content-reccomender/data/raw_ingest/discovered_videos.json", "w") as f:
    json.dump(results, f, indent=2)

print("Done. Saved to discovered_videos.json")
