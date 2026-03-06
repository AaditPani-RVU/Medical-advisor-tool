import requests
import json

diseases = [
    "diabetes", "asthma", "hypertension", "arthritis", "depression", 
    "anxiety", "migraine", "back-pain", "allergies", "obesity", 
    "cancer", "flu", "common-cold", "pneumonia", "bronchitis",
    "chickenpox", "measles", "mumps", "rubella", "whooping-cough",
    "tuberculosis", "malaria", "dengue", "cholera", "typhoid",
    "hepatitis-a", "hepatitis-b", "hepatitis-c", "hiv-aids", "syphilis",
    "gonorrhoea", "chlamydia", "herpes", "hpv", "scabies",
    "head-lice", "ringworm", "athletes-foot", "eczema", "psoriasis",
    "acne", "rosacea", "vitiligo", "alopecia", "dandruff",
    "glaucoma", "cataracts", "macular-degeneration", "conjunctivitis", "stye",
    "ear-infection", "tinnitus", "vertigo", "hearing-loss", "tonsillitis",
    "strep-throat", "sinusitis", "laryngitis", "sleep-apnoea", "insomnia",
    "narcolepsy", "restless-legs-syndrome", "epilepsy", "parkinsons-disease", "alzheimers-disease",
    "multiple-sclerosis", "stroke", "migraine", "tension-type-headache", "cluster-headache",
    "heart-attack", "angina", "heart-failure", "arrhythmia", "atrial-fibrillation",
    "deep-vein-thrombosis", "pulmonary-embolism", "varicose-veins", "haemorrhoids", "anaemia",
    "leukaemia", "lymphoma", "myeloma", "haemophilia", "sickle-cell-disease",
    "thalassaemia", "peptic-ulcer", "gastro-oesophageal-reflux-disease", "coeliac-disease", "crohns-disease",
    "ulcerative-colitis", "irritable-bowel-syndrome", "gallstones", "pancreatitis", "appendicitis"
]

results = []

print("Validating NHS URLs...")
# Using a connection pool to speed things up
with requests.Session() as session:
    session.headers.update({"User-Agent": "Mozilla/5.0"})
    for d in diseases:
        url = f"https://www.nhs.uk/conditions/{d}/"
        try:
            resp = session.head(url, timeout=5)
            if resp.status_code == 200:
                results.append({
                    "url": url,
                    "source_name": "NHS",
                    "source_tier": "verified_org"
                })
                print(f"Found: {url}")
            else:
                pass
        except Exception as e:
            pass

print(f"Validated {len(results)} valid NHS articles.")

with open("discovered_articles.json", "w") as f:
    json.dump(results, f, indent=2)

print("Saved to discovered_articles.json")
