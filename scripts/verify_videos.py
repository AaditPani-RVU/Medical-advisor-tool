"""Quick script to verify YouTube video IDs using oembed API."""
import httpx

test_ids = {
    # TED-Ed
    "yRh_ttnz49E": "TED-Ed cancer",
    "lXfEK8G8CUI": "TED-Ed vaccines",
    "RJ0cNRjsbl4": "TED-Ed kidney",
    "apkGDzRHfOM": "TED-Ed antibiotics",
    "WVTc6fLf7wU": "TED-Ed allergies",
    # Mayo
    "wDUzG2lMOdY": "Mayo heart",
    "6RzDa94n0Fs": "Mayo diabetes", 
    "sW2pUH7hY_E": "Mayo migraine",
    "NJgBuMsEpQQ": "Mayo BP",
    # Cleveland
    "V_qlr38-MnE": "Cleveland diabetes",
    "tY2M1Z3e5Nk": "Cleveland COPD",
    "cPij9MTeVl0": "Cleveland anemia",
    "S6u-6sDIGpg": "Cleveland thyroid",
    # JHU
    "MxqcllaMV6o": "JHU asthma",
    "4n_BvoFpat4": "JHU lupus",
    # WHO
    "BtN-goy9VOY": "WHO dengue",
    "5DGwOJXSxqg": "WHO malaria",
    "OOJqHPfG7pA": "WHO TB",
    # Osmosis
    "dBnniua6-oM": "Osmosis stroke",
    "GQoeX8WRa28": "Osmosis hepatitis",
    "uhJiR3GZ2Vg": "Osmosis kidney",
    "hA3VfraeZSI": "Osmosis anemia",
    "dU4w0aE_8w0": "Osmosis arthritis",
    # Nucleus
    "4fTUvJMvbUE": "Nucleus fracture",
    "Y-Is8RNq_qA": "Nucleus heart attack",
    "Ls7NAmIaJE0": "Nucleus burns",
    # Khan
    "K0GDLKM2Jc4": "Khan immune",
    "8ARb8Uy0Igw": "Khan heart",
    # NHS
    "TWiEwGr9MoE": "NHS depression",
    "lpc6oYiTkws": "NHS anxiety",
    # Indian
    "aqHljWIpOEE": "Apollo dengue",
    "N6Z-6cUNzJM": "Narayana diabetes",
    "I9eFIJSMHlQ": "Medanta heart",
    "hBsXikMh_Rw": "Paulose typhoid",
    "KJyEVD1rHBc": "Shomu cholera",
}

working = []
broken = []

for vid, desc in test_ids.items():
    url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={vid}&format=json"
    try:
        r = httpx.get(url, timeout=5.0)
        if r.status_code == 200:
            data = r.json()
            title = data.get("title", "?")
            channel = data.get("author_name", "?")
            working.append((vid, title, channel))
            print(f"  OK: {vid} | {channel} | {title}")
        else:
            broken.append((vid, desc, r.status_code))
            print(f"  BROKEN ({r.status_code}): {vid} ({desc})")
    except Exception as e:
        broken.append((vid, desc, str(e)))
        print(f"  ERROR: {vid} ({desc})")

print(f"\n=== {len(working)} working, {len(broken)} broken ===")
