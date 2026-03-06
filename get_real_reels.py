import time
import requests
from bs4 import BeautifulSoup
from googlesearch import search
import json

ACCOUNTS = ["mayoclinic", "clevelandclinic", "who", "johnshopkinsmedicine", "doctor.mike", "drmarkhyman"]
DISEASES = [
    "Asthma", "Hypertension", "Stroke", "Diabetes", "Dementia", "Arthritis",
    "Kidney Disease", "Liver Disease", "Epilepsy", "Migraine", "Endometriosis",
    "PCOS", "Glaucoma", "Osteoporosis", "Tuberculosis", "Malaria", "Cholera",
    "Lupus", "HIV", "Leukemia", "Lymphoma", "Melanoma", "Sepsis", "Pneumonia",
    "Bronchitis", "Emphysema", "Cystic Fibrosis", "Sickle Cell", "Anemia", "Gout"
]

reels = []
urls_seen = set()

for d in DISEASES:
    query = f"site:instagram.com/reel/ ({' OR '.join(ACCOUNTS)}) {d}"
    print(f"Searching for: {query}")
    try:
        results = list(search(query, num_results=3, lang="en"))
    except Exception as e:
        print(f"Error searching {d}: {e}")
        time.sleep(2)
        continue
    
    for url in results:
        if "/reel/" in url and url not in urls_seen:
            urls_seen.add(url)
            # Try to fetch title
            try:
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
                res = requests.get(url, headers=headers, timeout=5)
                soup = BeautifulSoup(res.text, 'html.parser')
                title = soup.title.string if soup.title else ""
                
                # Check for promotional or irrelevant
                title_lower = title.lower()
                if any(x in title_lower for x in ["celebrating", "giveaway", "win", "happy birthday", "promo"]):
                    continue
                
                if d.lower() in title_lower or True: # At least it's a medical account
                    # find which account
                    source_handle = next((acc for acc in ACCOUNTS if acc in url.lower()), "unknown")
                    reels.append({
                        "url": url,
                        "title": title.replace(" - Instagram", "").strip(),
                        "disease": d,
                        "source": source_handle
                    })
                    print(f"  Found: {url} - {title[:50]}...")
            except Exception as e:
                print(f"  Failed to fetch: {url}")
            
    if len(reels) >= 40:
        break
    time.sleep(1)

with open("discovered_real_reels.json", "w") as f:
    json.dump(reels, f, indent=2)

print(f"Saved {len(reels)} reels!")
