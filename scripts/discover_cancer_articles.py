import json

cancers = [
    "breast", "lung", "prostate", "colorectal", "colon",
    "bowel", "melanoma", "skin", "bladder", "non-hodgkin",
    "kidney", "renal", "endometrial", "uterine", "leukemia",
    "pancreatic", "thyroid", "liver", "hepatic", "brain-tumor",
    "brain", "ovarian", "cervical", "stomach", "gastric",
    "esophageal", "esophagus", "gallbladder", "testicular", "bone",
    "osteosarcoma", "sarcoma", "multiple-myeloma", "myeloma", "hodgkin",
    "throat", "laryngeal", "oral", "mouth", "mesothelioma", "neuroblastoma",
    "retinoblastoma", "vulvar", "vaginal", "anal", "penile",
    "bile-duct", "adrenal", "pituitary", "spinal"
]

results = []
for c in cancers:
    url = f"https://www.cdc.gov/cancer/{c}/"
    results.append({
        "url": url,
        "source_name": "CDC",
        "source_tier": "verified_org"
    })

with open("d:/verified-healthcare-content-reccomender/discovered_cancer_articles.json", "w") as f:
    json.dump(results, f, indent=2)

print("Generated CDC cancer article links.")
