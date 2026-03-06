import subprocess
import json
import time

cancers = [
    "breast cancer", "lung cancer", "prostate cancer", "colorectal cancer", "colon cancer",
    "bowel cancer", "melanoma", "skin cancer", "bladder cancer", "non-hodgkin lymphoma",
    "kidney cancer", "renal cancer", "endometrial cancer", "uterine cancer", "leukemia",
    "pancreatic cancer", "thyroid cancer", "liver cancer", "hepatic cancer", "brain tumor",
    "brain cancer", "ovarian cancer", "cervical cancer", "stomach cancer", "gastric cancer",
    "esophageal cancer", "gallbladder cancer", "testicular cancer", "bone cancer",
    "osteosarcoma", "sarcoma", "multiple myeloma", "hodgkin lymphoma", "throat cancer",
    "laryngeal cancer", "oral cancer", "mouth cancer", "mesothelioma", "neuroblastoma",
    "retinoblastoma", "vulvar cancer", "vaginal cancer", "anal cancer", "penile cancer",
    "bile duct cancer", "adrenal cancer", "pituitary tumor", "spinal cord tumor"
]

channels = [
    "Mayo Clinic", "Cleveland Clinic", "NHS", "Johns Hopkins Medicine", "MD Anderson Cancer Center"
]

results = []
print(f"Starting discovery for {len(cancers)} cancer types...")

for c in cancers:
    for channel in channels:
        query = f"{c} {channel}"
        print(f"Searching: {query}")
        try:
            cmd = ["yt-dlp", f"ytsearch2:{query}", "--dump-json", "--lazy-playlist", "--no-warnings"]
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, stderr = process.communicate()
            
            for line in stdout.splitlines():
                if not line.strip(): continue
                data = json.loads(line)
                vid_id = data.get("id")
                title = data.get("title")
                uploader = data.get("uploader")
                duration = data.get("duration", 0)
                
                # Check channel match
                if channel.lower() not in uploader.lower():
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
                    "disease": "cancer" # We map all to the general "cancer" topic tag area
                })
        except Exception as e:
            print(f"Error on {query}: {e}")
        time.sleep(1)

print(f"Discovered {len(results)} videos.")
with open("discovered_cancer_videos.json", "w") as f:
    json.dump(results, f, indent=2)

print("Saved to discovered_cancer_videos.json")
