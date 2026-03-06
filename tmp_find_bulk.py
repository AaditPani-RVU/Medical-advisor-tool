"""
Comprehensive scraper to find 50+ verified YouTube health video IDs.
Strategy: Scrape TED-Ed health lesson pages (most reliable source), 
plus Mayo Clinic disease pages, and verify all IDs via noembed.com.
"""
import urllib.request
import json
import re
import time

ALREADY_HAVE = {
    "ycX1BPOwGwM", "E6lMGCoRBPA", "wXk1Nj28Hm4", "kmDKDTbg_78", "12Ec8VFBBJU",
    "W0GpIMNTPYg", "rb7TVW77ZCs", "OcigJn8UJNQ", "yJXTXN4xrI8", "-NJm4TJ2it0",
    "3_PYnWVoUzM", "z-IR48Mb3W0", "gVdY9KXF_Sg", "xvjK-4NXRsM", "PzfLDi-sL3w",
    "xyQY8a-ng6g",
}

def check_noembed(vid):
    try:
        url = f"https://noembed.com/embed?url=https://www.youtube.com/watch?v={vid}"
        resp = urllib.request.urlopen(url, timeout=10)
        data = json.loads(resp.read())
        if "error" in data:
            return False, "", ""
        return True, data.get("title", ""), data.get("author_name", "")
    except:
        return False, "", ""

def extract_video_ids(text):
    patterns = [
        r'youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})',
        r'youtube\.com/embed/([a-zA-Z0-9_-]{11})',
        r'youtu\.be/([a-zA-Z0-9_-]{11})',
    ]
    ids = set()
    for p in patterns:
        ids.update(re.findall(p, text))
    return ids

def fetch_page(url):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        resp = urllib.request.urlopen(req, timeout=10)
        return resp.read().decode('utf-8', errors='ignore')
    except:
        return ""

def extract_ted_ed_lesson_links(text):
    """Extract TED-Ed lesson URLs from a page."""
    pattern = r'href="(/lessons/[^"]+)"'
    return list(set(re.findall(pattern, text)))

# Phase 1: Get ALL TED-Ed health lesson URLs from their listing pages
print("=== Phase 1: Finding TED-Ed health lesson URLs ===")
ted_ed_lessons = set()

# Scrape multiple pages of TED-Ed health lessons
for page_num in range(1, 8):
    url = f"https://ed.ted.com/lessons?direction=desc&sort=publish-date&category=health&page={page_num}"
    content = fetch_page(url)
    if content:
        links = extract_ted_ed_lesson_links(content)
        for link in links:
            if '/lessons/' in link:
                ted_ed_lessons.add(f"https://ed.ted.com{link}")
        print(f"  Page {page_num}: found {len(links)} lesson links (total unique: {len(ted_ed_lessons)})")
    time.sleep(0.5)

# Also get science/biology category lessons
for page_num in range(1, 5):
    url = f"https://ed.ted.com/lessons?direction=desc&sort=publish-date&category=science-and-technology&page={page_num}"
    content = fetch_page(url)
    if content:
        links = extract_ted_ed_lesson_links(content)
        for link in links:
            if '/lessons/' in link:
                ted_ed_lessons.add(f"https://ed.ted.com{link}")
        print(f"  Sci page {page_num}: found {len(links)} links (total unique: {len(ted_ed_lessons)})")
    time.sleep(0.5)

# Phase 2: Additional known TED-Ed health lessons from curated list
known_ted_ed = [
    "https://ed.ted.com/lessons/what-causes-an-ear-infection-sho-hatakeyama",
    "https://ed.ted.com/lessons/how-do-your-hormones-work-emma-bryce",
    "https://ed.ted.com/lessons/what-happens-to-your-brain-during-a-migraine-marianne-schwarz",
    "https://ed.ted.com/lessons/how-do-blood-transfusions-work-bill-schutt",
    "https://ed.ted.com/lessons/what-makes-muscles-grow-jeffrey-siegel",
    "https://ed.ted.com/lessons/what-causes-heartburn-rusha-modi",
    "https://ed.ted.com/lessons/how-do-vitamins-work-ginnie-trinh-nguyen",
    "https://ed.ted.com/lessons/what-causes-body-odor-mel-rosenberg",
    "https://ed.ted.com/lessons/how-does-your-body-process-medicine-celine-valery",
    "https://ed.ted.com/lessons/what-causes-insomnia-dan-kwartler",
    "https://ed.ted.com/lessons/is-it-bad-to-hold-your-pee-heba-shaheed",
    "https://ed.ted.com/lessons/what-does-the-liver-do-emma-bryce",
    "https://ed.ted.com/lessons/what-does-the-pancreas-do-emma-bryce",
    "https://ed.ted.com/lessons/how-do-your-kidneys-work-emma-bryce",
    "https://ed.ted.com/lessons/what-happens-when-your-dna-is-damaged-monica-menesini",
    "https://ed.ted.com/lessons/how-does-your-immune-system-work-emma-bryce",
    "https://ed.ted.com/lessons/what-causes-seizures-christopher-e-gaw",
    "https://ed.ted.com/lessons/what-causes-opioid-addiction-and-why-is-it-so-tough-to-combat-mike-davis",
    "https://ed.ted.com/lessons/how-do-lungs-work-emma-bryce",
    "https://ed.ted.com/lessons/what-happens-when-you-remove-the-appendix-emma-bryce",
    "https://ed.ted.com/lessons/what-causes-cavities-mel-rosenberg",
    "https://ed.ted.com/lessons/are-there-bacteria-on-your-brain",
    "https://ed.ted.com/lessons/what-is-a-coronavirus-elizabeth-cox",
    "https://ed.ted.com/lessons/how-does-anesthesia-work-steven-zheng",
    "https://ed.ted.com/lessons/the-hidden-side-of-clinical-trials-sile-lane",
    "https://ed.ted.com/lessons/how-does-the-thyroid-manage-your-metabolism-emma-bryce",
    "https://ed.ted.com/lessons/what-is-leukemia-danilo-allegra-and-dania-puggioni",
    "https://ed.ted.com/lessons/why-do-we-itch-emma-bryce",
    "https://ed.ted.com/lessons/what-causes-constipation-heba-shaheed",
    "https://ed.ted.com/lessons/what-happens-during-a-fever-christian-moro",
    "https://ed.ted.com/lessons/what-happens-when-you-get-heat-stroke-douglas-j-casa",
    "https://ed.ted.com/lessons/how-do-brain-scans-work-john-borghi-and-elizabeth-beam",
    "https://ed.ted.com/lessons/what-causes-panic-attacks-and-how-can-you-prevent-them-cindy-j-aaronson",
    "https://ed.ted.com/lessons/what-happens-to-your-brain-when-you-re-in-love",
    "https://ed.ted.com/lessons/how-does-heart-transplant-work-roni-shanoada",
    "https://ed.ted.com/lessons/what-causes-sore-throats-avinash-sud",
    "https://ed.ted.com/lessons/why-is-meningitis-so-dangerous-melvin-sanicas",
    "https://ed.ted.com/lessons/how-menstruation-works-emma-bryce",
    "https://ed.ted.com/lessons/what-causes-headaches-dan-kwartler",
    "https://ed.ted.com/lessons/what-is-hpv-and-how-can-you-protect-yourself-from-it-emma-bryce",
    "https://ed.ted.com/lessons/how-do-your-brain-s-executive-functions-work-sabine-doebel",
    "https://ed.ted.com/lessons/what-causes-food-allergies",
]
ted_ed_lessons.update(known_ted_ed)

# Phase 3: Mayo Clinic disease pages
mayo_pages = [
    "https://www.mayoclinic.org/diseases-conditions/coronary-artery-disease/symptoms-causes/syc-20350613",
    "https://www.mayoclinic.org/diseases-conditions/type-2-diabetes/symptoms-causes/syc-20351193",
    "https://www.mayoclinic.org/diseases-conditions/asthma/symptoms-causes/syc-20369653",
    "https://www.mayoclinic.org/diseases-conditions/celiac-disease/symptoms-causes/syc-20352220",
    "https://www.mayoclinic.org/diseases-conditions/high-blood-pressure/symptoms-causes/syc-20373410",
    "https://www.mayoclinic.org/diseases-conditions/copd/symptoms-causes/syc-20353679",
    "https://www.mayoclinic.org/diseases-conditions/stroke/symptoms-causes/syc-20350113",
    "https://www.mayoclinic.org/diseases-conditions/depression/symptoms-causes/syc-20356007",
    "https://www.mayoclinic.org/diseases-conditions/anxiety/symptoms-causes/syc-20350961",
    "https://www.mayoclinic.org/diseases-conditions/pneumonia/symptoms-causes/syc-20354204",
    "https://www.mayoclinic.org/diseases-conditions/arthritis/symptoms-causes/syc-20350772",
    "https://www.mayoclinic.org/diseases-conditions/epilepsy/symptoms-causes/syc-20350093",
    "https://www.mayoclinic.org/diseases-conditions/crohn-disease/symptoms-causes/syc-20353304",
    "https://www.mayoclinic.org/diseases-conditions/osteoporosis/symptoms-causes/syc-20351968",
    "https://www.mayoclinic.org/diseases-conditions/sleep-apnea/symptoms-causes/syc-20377631",
    "https://www.mayoclinic.org/diseases-conditions/alzheimers-disease/symptoms-causes/syc-20350447",
    "https://www.mayoclinic.org/diseases-conditions/lupus/symptoms-causes/syc-20365789",
    "https://www.mayoclinic.org/diseases-conditions/multiple-sclerosis/symptoms-causes/syc-20350269",
    "https://www.mayoclinic.org/diseases-conditions/skin-cancer/symptoms-causes/syc-20377605",
    "https://www.mayoclinic.org/diseases-conditions/breast-cancer/symptoms-causes/syc-20352470",
]

print(f"\n=== Phase 2: Scraping {len(ted_ed_lessons)} TED-Ed pages + {len(mayo_pages)} Mayo pages ===")

all_found = {}
all_pages = list(ted_ed_lessons) + mayo_pages

for i, page_url in enumerate(all_pages):
    content = fetch_page(page_url)
    if content:
        ids = extract_video_ids(content)
        for vid in ids:
            if vid not in all_found and vid not in ALREADY_HAVE:
                ok, title, author = check_noembed(vid)
                if ok:
                    all_found[vid] = {"title": title, "author": author, "source_url": page_url}
                    print(f"  [{len(all_found)}] {vid} -> {title} (by {author})")
                time.sleep(0.2)
    
    # Progress indicator every 20 pages
    if (i + 1) % 20 == 0:
        print(f"  ... processed {i + 1}/{len(all_pages)} pages, found {len(all_found)} videos so far")
    
    # Stop early if we have enough
    if len(all_found) >= 55:
        print(f"  Found enough videos ({len(all_found)}), stopping early")
        break

print(f"\n\n=== RESULTS: {len(all_found)} verified videos found ===\n")

# Output in the format needed for fetch_youtube.py
for vid, info in all_found.items():
    author = info['author']
    tier = "verified_org" if author in ["Mayo Clinic", "Cleveland Clinic", "Johns Hopkins Medicine", "NHS", "WHO"] else "verified_creator"
    title_escaped = info['title'].replace('"', '\\"')
    print(f'        {{"video_id": "{vid}", "title": "{title_escaped}", "channel_name": "{author}", "source_tier": "{tier}"}},')
