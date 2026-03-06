import ast
import json

with open("generated_mock_reels.py", "r", encoding="utf-8") as f:
    text = f.read()

reels = ast.literal_eval(text.split("NEW_REELS = ")[1])

# Medical keywords
medical_terms = ["therap", "cholesterol", "sugar", "diet", "health", "disease", "syndrome", "pain", "cancer", "heart", "brain", "lung", "liver", "kidney", "blood", "diabet", "asthma", "stroke", "dementia", "arthrit", "epilepsy", "migraine", "pcos", "glaucoma", "osteoporosis", "tuberculosis", "malaria", "cholera", "lupus", "hiv", "leukemia", "lymphoma", "melanoma", "sepsis", "pneumonia", "bronchitis", "emphysema", "cystic", "sickle", "anemia", "gout", "symptom", "treatment", "doctor", "medic", "patient", "pressure", "hypertension", "obesity", "weight", "virus", "infection", "vaccin", "surgery", "pill", "cure", "body", "muscle", "bone", "skin", "eye", "ear", "nose", "throat", "headache", "fever", "cough", "cold", "flu", "rs", "covid"]

filtered = []
for r in reels:
    title = r["title"].lower()
    
    is_educational = any(term in title for term in medical_terms)
    is_bad = any(x in title for x in ["celebrat", "win ", "giveaway", "podcast", "episode", "live", "q&a", "part 1", "part 2"])
    
    if is_educational and not is_bad:
        filtered.append(r)

if len(filtered) < 30:
    remaining = [r for r in reels if r not in filtered and not any(x in r["title"].lower() for x in ["celebrat", "win ", "giveaway", "podcast", "episode", "live", "q&a"])]
    filtered.extend(remaining[:30 - len(filtered)])

final_30 = filtered[:30]

# Ensure we have 30
if len(final_30) < 30:
    final_30.extend([r for r in reels if r not in final_30][:30 - len(final_30)])

# Inject to mock_instagram_ingest.py
with open("scripts/mock_instagram_ingest.py", "r", encoding="utf-8") as f:
    content = f.read()

# Make sure we don't inject multiple times easily if run accidentally
if "yt-dlp injected" not in content:
    dicts_str = ",\n    # yt-dlp injected reels\n    " + ",\n    ".join(repr(r) for r in final_30)
    new_content = content.replace("]\n\n\n\ndef main():", dicts_str + "\n]\n\n\n\ndef main():")

    with open("scripts/mock_instagram_ingest.py", "w", encoding="utf-8") as f:
        f.write(new_content)

    print(f"Successfully injected {len(final_30)} reels into scripts/mock_instagram_ingest.py")
else:
    print("Already injected!")
