"""
Web page fetcher — fetches content from allowlisted web pages.
"""

import httpx
import logging
from backend.core.settings import get_sources_allowlist
from backend.core.utils import is_url_from_allowlist, parse_date
from backend.ingest.extract_text import extract_text_from_html

logger = logging.getLogger(__name__)

# ── Seed URLs organized by source and topic ─────────────────
# Each entry: url, source_name, source_tier

DEFAULT_SEED_URLS = [
    # ================================================================
    # INDIA — Government & National Portals
    # ================================================================
    {
        "url": "https://www.nhp.gov.in/disease/digestive/stomach/peptic-ulcer-disease",
        "source_name": "National Health Portal India",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.nhp.gov.in/disease/cardiovascular/hypertension",
        "source_name": "National Health Portal India",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.nhp.gov.in/disease/endocrinal/diabetes",
        "source_name": "National Health Portal India",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.nhp.gov.in/disease/respiratory/asthma",
        "source_name": "National Health Portal India",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.nhp.gov.in/disease/neurological/epilepsy",
        "source_name": "National Health Portal India",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.nhp.gov.in/disease/communicable-disease/dengue",
        "source_name": "National Health Portal India",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.nhp.gov.in/disease/communicable-disease/malaria",
        "source_name": "National Health Portal India",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.nhp.gov.in/disease/communicable-disease/tuberculosis",
        "source_name": "National Health Portal India",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.nhp.gov.in/disease/musculoskeletal/arthritis",
        "source_name": "National Health Portal India",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.nhp.gov.in/disease/kidney/chronic-kidney-disease",
        "source_name": "National Health Portal India",
        "source_tier": "verified_org",
    },

    # ================================================================
    # INDIA — Premier Hospitals (Health Libraries)
    # ================================================================
    {
        "url": "https://www.apollohospitals.com/patient-care/health-and-lifestyle/diseases-and-conditions/diabetes",
        "source_name": "Apollo Hospitals",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.apollohospitals.com/patient-care/health-and-lifestyle/diseases-and-conditions/heart-disease",
        "source_name": "Apollo Hospitals",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.apollohospitals.com/patient-care/health-and-lifestyle/diseases-and-conditions/dengue",
        "source_name": "Apollo Hospitals",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.medanta.org/diseases/osteoarthritis",
        "source_name": "Medanta",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.medanta.org/diseases/kidney-stones",
        "source_name": "Medanta",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.medanta.org/diseases/liver-cirrhosis",
        "source_name": "Medanta",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.fortishealthcare.com/blogs/diseases-conditions",
        "source_name": "Fortis Healthcare",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.narayanahealth.org/blog/understanding-diabetes",
        "source_name": "Narayana Health",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.maxhealthcare.in/blogs/kidney-diseases",
        "source_name": "Max Healthcare",
        "source_tier": "verified_org",
    },

    # ================================================================
    # INTERNATIONAL — Core Health Organizations
    # ================================================================
    {
        "url": "https://www.cdc.gov/heart-disease/about/index.html",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/diabetes/about/index.html",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/dengue/about/index.html",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/malaria/about/index.html",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.who.int/news-room/fact-sheets/detail/cardiovascular-diseases-(cvds)",
        "source_name": "WHO",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.who.int/news-room/fact-sheets/detail/dengue-and-severe-dengue",
        "source_name": "WHO",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.who.int/news-room/fact-sheets/detail/malaria",
        "source_name": "WHO",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.who.int/news-room/fact-sheets/detail/diabetes",
        "source_name": "WHO",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.who.int/news-room/fact-sheets/detail/burns",
        "source_name": "WHO",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.who.int/news-room/fact-sheets/detail/snakebite-envenoming",
        "source_name": "WHO",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.nhs.uk/conditions/type-2-diabetes/",
        "source_name": "NHS",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.nhs.uk/conditions/broken-arm-or-wrist/",
        "source_name": "NHS",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.nhs.uk/conditions/sprains-and-strains/",
        "source_name": "NHS",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.nhs.uk/conditions/burns-and-scalds/",
        "source_name": "NHS",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.nhs.uk/conditions/head-injury-and-concussion/",
        "source_name": "NHS",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.nhs.uk/mental-health/conditions/depression-in-adults/overview/",
        "source_name": "NHS",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.nhs.uk/conditions/chronic-kidney-disease/",
        "source_name": "NHS",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.nhs.uk/conditions/autoimmune-hepatitis/",
        "source_name": "NHS",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.nhs.uk/conditions/lupus/",
        "source_name": "NHS",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.nhs.uk/conditions/rheumatoid-arthritis/",
        "source_name": "NHS",
        "source_tier": "verified_org",
    },

    # ================================================================
    # INTERNATIONAL — Specialty Sources
    # ================================================================

    # Mayo Clinic
    {
        "url": "https://www.mayoclinic.org/diseases-conditions/asthma/symptoms-causes/syc-20369653",
        "source_name": "Mayo Clinic",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.mayoclinic.org/diseases-conditions/sprain/symptoms-causes/syc-20377938",
        "source_name": "Mayo Clinic",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.mayoclinic.org/diseases-conditions/concussion/symptoms-causes/syc-20355594",
        "source_name": "Mayo Clinic",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.mayoclinic.org/diseases-conditions/chronic-kidney-disease/symptoms-causes/syc-20354521",
        "source_name": "Mayo Clinic",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.mayoclinic.org/diseases-conditions/cirrhosis/symptoms-causes/syc-20351487",
        "source_name": "Mayo Clinic",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.mayoclinic.org/diseases-conditions/lupus/symptoms-causes/syc-20365789",
        "source_name": "Mayo Clinic",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.mayoclinic.org/diseases-conditions/sickle-cell-anemia/symptoms-causes/syc-20355876",
        "source_name": "Mayo Clinic",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.mayoclinic.org/diseases-conditions/epilepsy/symptoms-causes/syc-20350093",
        "source_name": "Mayo Clinic",
        "source_tier": "verified_org",
    },

    # Cleveland Clinic
    {
        "url": "https://my.clevelandclinic.org/health/diseases/7104-diabetes",
        "source_name": "Cleveland Clinic",
        "source_tier": "verified_org",
    },
    {
        "url": "https://my.clevelandclinic.org/health/diseases/15096-sports-injuries",
        "source_name": "Cleveland Clinic",
        "source_tier": "verified_org",
    },
    {
        "url": "https://my.clevelandclinic.org/health/diseases/17689-anemia",
        "source_name": "Cleveland Clinic",
        "source_tier": "verified_org",
    },
    {
        "url": "https://my.clevelandclinic.org/health/diseases/15850-autoimmune-diseases",
        "source_name": "Cleveland Clinic",
        "source_tier": "verified_org",
    },

    # Johns Hopkins
    {
        "url": "https://www.hopkinsmedicine.org/health/conditions-and-diseases/diabetes",
        "source_name": "Johns Hopkins Medicine",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.hopkinsmedicine.org/health/conditions-and-diseases/hepatitis",
        "source_name": "Johns Hopkins Medicine",
        "source_tier": "verified_org",
    },

    # MedlinePlus
    {
        "url": "https://medlineplus.gov/diabetes.html",
        "source_name": "MedlinePlus",
        "source_tier": "verified_org",
    },
    {
        "url": "https://medlineplus.gov/kidneydiseases.html",
        "source_name": "MedlinePlus",
        "source_tier": "verified_org",
    },
    {
        "url": "https://medlineplus.gov/rarediseases.html",
        "source_name": "MedlinePlus",
        "source_tier": "verified_org",
    },
    {
        "url": "https://medlineplus.gov/poisoning.html",
        "source_name": "MedlinePlus",
        "source_tier": "verified_org",
    },
    {
        "url": "https://medlineplus.gov/sportsinjuries.html",
        "source_name": "MedlinePlus",
        "source_tier": "verified_org",
    },
    {
        "url": "https://medlineplus.gov/burns.html",
        "source_name": "MedlinePlus",
        "source_tier": "verified_org",
    },

    # NIH Specialty Institutes
    {
        "url": "https://www.ninds.nih.gov/health-information/disorders/epilepsy-and-seizures",
        "source_name": "NINDS (NIH)",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.ninds.nih.gov/health-information/disorders/traumatic-brain-injury",
        "source_name": "NINDS (NIH)",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.niddk.nih.gov/health-information/kidney-disease",
        "source_name": "NIDDK (NIH)",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.niddk.nih.gov/health-information/liver-disease",
        "source_name": "NIDDK (NIH)",
        "source_tier": "verified_org",
    },
    {
        "url": "https://rarediseases.org/for-patients-and-families/information-resources/",
        "source_name": "NORD",
        "source_tier": "verified_org",
    },

    # Orthopedic (AAOS)
    {
        "url": "https://orthoinfo.aaos.org/en/diseases--conditions/sprains-strains-and-other-soft-tissue-injuries",
        "source_name": "OrthoInfo (AAOS)",
        "source_tier": "verified_org",
    },
    {
        "url": "https://orthoinfo.aaos.org/en/diseases--conditions/fractures-broken-bones/",
        "source_name": "OrthoInfo (AAOS)",
        "source_tier": "verified_org",
    },
    {
        "url": "https://orthoinfo.aaos.org/en/staying-healthy/preventing-sports-injuries/",
        "source_name": "OrthoInfo (AAOS)",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.nhs.uk/conditions/diabetes/",
        "source_name": "NHS",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.nhs.uk/conditions/asthma/",
        "source_name": "NHS",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.nhs.uk/conditions/high-blood-pressure-hypertension/",
        "source_name": "NHS",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.nhs.uk/conditions/arthritis/",
        "source_name": "NHS",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.nhs.uk/conditions/depression/",
        "source_name": "NHS",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.nhs.uk/conditions/migraine/",
        "source_name": "NHS",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.nhs.uk/conditions/back-pain/",
        "source_name": "NHS",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.nhs.uk/conditions/allergies/",
        "source_name": "NHS",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.nhs.uk/conditions/obesity/",
        "source_name": "NHS",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.nhs.uk/conditions/flu/",
        "source_name": "NHS",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.nhs.uk/conditions/common-cold/",
        "source_name": "NHS",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.nhs.uk/conditions/pneumonia/",
        "source_name": "NHS",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.nhs.uk/conditions/bronchitis/",
        "source_name": "NHS",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.nhs.uk/conditions/chickenpox/",
        "source_name": "NHS",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.nhs.uk/conditions/measles/",
        "source_name": "NHS",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.nhs.uk/conditions/tuberculosis/",
        "source_name": "NHS",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.nhs.uk/conditions/malaria/",
        "source_name": "NHS",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.nhs.uk/conditions/dengue/",
        "source_name": "NHS",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.nhs.uk/conditions/cholera/",
        "source_name": "NHS",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.nhs.uk/conditions/typhoid/",
        "source_name": "NHS",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.nhs.uk/conditions/hepatitis-a/",
        "source_name": "NHS",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.nhs.uk/conditions/hepatitis-b/",
        "source_name": "NHS",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.nhs.uk/conditions/hepatitis-c/",
        "source_name": "NHS",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.nhs.uk/conditions/hiv-aids/",
        "source_name": "NHS",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.nhs.uk/conditions/syphilis/",
        "source_name": "NHS",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.nhs.uk/conditions/gonorrhoea/",
        "source_name": "NHS",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.nhs.uk/conditions/chlamydia/",
        "source_name": "NHS",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.nhs.uk/conditions/herpes/",
        "source_name": "NHS",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.nhs.uk/conditions/scabies/",
        "source_name": "NHS",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.nhs.uk/conditions/head-lice/",
        "source_name": "NHS",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.nhs.uk/conditions/ringworm/",
        "source_name": "NHS",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.nhs.uk/conditions/eczema/",
        "source_name": "NHS",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.nhs.uk/conditions/psoriasis/",
        "source_name": "NHS",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.nhs.uk/conditions/acne/",
        "source_name": "NHS",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.nhs.uk/conditions/rosacea/",
        "source_name": "NHS",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.nhs.uk/conditions/vitiligo/",
        "source_name": "NHS",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.nhs.uk/conditions/glaucoma/",
        "source_name": "NHS",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.nhs.uk/conditions/cataracts/",
        "source_name": "NHS",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.nhs.uk/conditions/macular-degeneration/",
        "source_name": "NHS",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.nhs.uk/conditions/conjunctivitis/",
        "source_name": "NHS",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.nhs.uk/conditions/ear-infection/",
        "source_name": "NHS",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.nhs.uk/conditions/tinnitus/",
        "source_name": "NHS",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.nhs.uk/conditions/vertigo/",
        "source_name": "NHS",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.nhs.uk/conditions/hearing-loss/",
        "source_name": "NHS",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.nhs.uk/conditions/tonsillitis/",
        "source_name": "NHS",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.nhs.uk/conditions/strep-throat/",
        "source_name": "NHS",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.nhs.uk/conditions/sinusitis/",
        "source_name": "NHS",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.nhs.uk/conditions/laryngitis/",
        "source_name": "NHS",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.nhs.uk/conditions/sleep-apnoea/",
        "source_name": "NHS",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.nhs.uk/conditions/insomnia/",
        "source_name": "NHS",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.nhs.uk/conditions/epilepsy/",
        "source_name": "NHS",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.nhs.uk/conditions/parkinsons-disease/",
        "source_name": "NHS",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.nhs.uk/conditions/alzheimers-disease/",
        "source_name": "NHS",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.nhs.uk/conditions/multiple-sclerosis/",
        "source_name": "NHS",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.nhs.uk/conditions/stroke/",
        "source_name": "NHS",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.nhs.uk/conditions/heart-attack/",
        "source_name": "NHS",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.nhs.uk/conditions/angina/",
        "source_name": "NHS",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.nhs.uk/conditions/heart-failure/",
        "source_name": "NHS",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.nhs.uk/conditions/deep-vein-thrombosis/",
        "source_name": "NHS",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.nhs.uk/conditions/pulmonary-embolism/",
        "source_name": "NHS",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.nhs.uk/conditions/varicose-veins/",
        "source_name": "NHS",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.nhs.uk/conditions/haemorrhoids/",
        "source_name": "NHS",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.nhs.uk/conditions/anaemia/",
        "source_name": "NHS",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.nhs.uk/conditions/leukaemia/",
        "source_name": "NHS",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.nhs.uk/conditions/lymphoma/",
        "source_name": "NHS",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.nhs.uk/conditions/myeloma/",
        "source_name": "NHS",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.nhs.uk/conditions/haemophilia/",
        "source_name": "NHS",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.nhs.uk/conditions/sickle-cell-disease/",
        "source_name": "NHS",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.nhs.uk/conditions/peptic-ulcer/",
        "source_name": "NHS",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.nhs.uk/conditions/coeliac-disease/",
        "source_name": "NHS",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.nhs.uk/conditions/crohns-disease/",
        "source_name": "NHS",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.nhs.uk/conditions/ulcerative-colitis/",
        "source_name": "NHS",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.nhs.uk/conditions/irritable-bowel-syndrome/",
        "source_name": "NHS",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.nhs.uk/conditions/gallstones/",
        "source_name": "NHS",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.nhs.uk/conditions/pancreatitis/",
        "source_name": "NHS",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.nhs.uk/conditions/appendicitis/",
        "source_name": "NHS",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/diabetes/about/index.html",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/asthma/about/index.html",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/heart-disease/about/index.html",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/arthritis/about/index.html",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/depression/about/index.html",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/migraine/about/index.html",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/back-pain/about/index.html",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/allergies/about/index.html",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/obesity/about/index.html",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/flu/about/index.html",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/common-cold/about/index.html",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/pneumonia/about/index.html",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/bronchitis/about/index.html",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/chickenpox/about/index.html",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/measles/about/index.html",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/tuberculosis/about/index.html",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/malaria/about/index.html",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/dengue/about/index.html",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cholera/about/index.html",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/typhoid/about/index.html",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/hepatitis/about/index.html",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/hiv/about/index.html",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/syphilis/about/index.html",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/gonorrhea/about/index.html",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/chlamydia/about/index.html",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/herpes/about/index.html",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/scabies/about/index.html",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/head-lice/about/index.html",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/ringworm/about/index.html",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/eczema/about/index.html",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/psoriasis/about/index.html",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/acne/about/index.html",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/rosacea/about/index.html",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/vitiligo/about/index.html",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/glaucoma/about/index.html",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cataracts/about/index.html",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/macular-degeneration/about/index.html",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/conjunctivitis/about/index.html",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/ear-infection/about/index.html",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/tinnitus/about/index.html",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/vertigo/about/index.html",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/hearing-loss/about/index.html",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/tonsillitis/about/index.html",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/strep-throat/about/index.html",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/sinusitis/about/index.html",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/laryngitis/about/index.html",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/sleep-apnea/about/index.html",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/insomnia/about/index.html",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/epilepsy/about/index.html",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/parkinsons-disease/about/index.html",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/alzheimers-disease/about/index.html",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/multiple-sclerosis/about/index.html",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/stroke/about/index.html",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/heart-attack/about/index.html",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/angina/about/index.html",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/heart-failure/about/index.html",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/dvt/about/index.html",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/pulmonary-embolism/about/index.html",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/varicose-veins/about/index.html",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/hemorrhoids/about/index.html",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/anemia/about/index.html",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/leukemia/about/index.html",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/lymphoma/about/index.html",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/myeloma/about/index.html",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/hemophilia/about/index.html",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/sickle-cell-disease/about/index.html",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/peptic-ulcer/about/index.html",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/celiac-disease/about/index.html",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/crohns-disease/about/index.html",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/ulcerative-colitis/about/index.html",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/ibs/about/index.html",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/gallstones/about/index.html",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/pancreatitis/about/index.html",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/appendicitis/about/index.html",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cancer/breast/",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cancer/lung/",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cancer/prostate/",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cancer/colorectal/",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cancer/colon/",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cancer/bowel/",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cancer/melanoma/",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cancer/skin/",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cancer/bladder/",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cancer/non-hodgkin/",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cancer/kidney/",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cancer/renal/",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cancer/endometrial/",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cancer/uterine/",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cancer/leukemia/",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cancer/pancreatic/",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cancer/thyroid/",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cancer/liver/",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cancer/hepatic/",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cancer/brain-tumor/",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cancer/brain/",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cancer/ovarian/",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cancer/cervical/",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cancer/stomach/",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cancer/gastric/",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cancer/esophageal/",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cancer/esophagus/",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cancer/gallbladder/",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cancer/testicular/",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cancer/bone/",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cancer/osteosarcoma/",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cancer/sarcoma/",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cancer/multiple-myeloma/",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cancer/myeloma/",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cancer/hodgkin/",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cancer/throat/",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cancer/laryngeal/",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cancer/oral/",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cancer/mouth/",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cancer/mesothelioma/",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cancer/neuroblastoma/",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cancer/retinoblastoma/",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cancer/vulvar/",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cancer/vaginal/",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cancer/anal/",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cancer/penile/",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cancer/bile-duct/",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cancer/adrenal/",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cancer/pituitary/",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cancer/spinal/",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cancer/breast/",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cancer/lung/",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cancer/prostate/",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cancer/colorectal/",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cancer/colon/",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cancer/bowel/",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cancer/melanoma/",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cancer/skin/",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cancer/bladder/",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cancer/non-hodgkin/",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cancer/kidney/",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cancer/renal/",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cancer/endometrial/",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cancer/uterine/",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cancer/leukemia/",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cancer/pancreatic/",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cancer/thyroid/",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cancer/liver/",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cancer/hepatic/",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cancer/brain-tumor/",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cancer/brain/",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cancer/ovarian/",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cancer/cervical/",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cancer/stomach/",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cancer/gastric/",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cancer/esophageal/",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cancer/esophagus/",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cancer/gallbladder/",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cancer/testicular/",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cancer/bone/",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cancer/osteosarcoma/",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cancer/sarcoma/",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cancer/multiple-myeloma/",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cancer/myeloma/",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cancer/hodgkin/",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cancer/throat/",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cancer/laryngeal/",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cancer/oral/",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cancer/mouth/",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cancer/mesothelioma/",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cancer/neuroblastoma/",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cancer/retinoblastoma/",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cancer/vulvar/",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cancer/vaginal/",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cancer/anal/",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cancer/penile/",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cancer/bile-duct/",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cancer/adrenal/",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cancer/pituitary/",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
    {
        "url": "https://www.cdc.gov/cancer/spinal/",
        "source_name": "CDC",
        "source_tier": "verified_org",
    },
]


def fetch_web_pages(seed_urls: list[dict] | None = None) -> list[dict]:
    """
    Fetch web pages from seed URLs. Only processes allowlisted domains.
    Returns content item dicts ready for DB insertion.
    """
    config = get_sources_allowlist()
    trusted_domains = config.get("trusted_domains", [])

    urls_to_fetch = seed_urls or DEFAULT_SEED_URLS
    items = []

    for page in urls_to_fetch:
        url = page.get("url", "")
        source_name = page.get("source_name", "Unknown")
        source_tier = page.get("source_tier", "verified_org")

        # Validate domain
        if not is_url_from_allowlist(url, trusted_domains):
            logger.warning(f"Skipping non-allowlisted URL: {url}")
            continue

        logger.info(f"Fetching web page: {url}")

        try:
            response = httpx.get(
                url,
                timeout=15.0,
                follow_redirects=True,
                headers={
                    "User-Agent": "VerifiedHealthContent/1.0 (Educational Research Bot)"
                },
            )
            response.raise_for_status()

            html = response.text
            title, text = extract_text_from_html(html)

            if not title:
                title = source_name + " — Health Content"
            if not text or len(text) < 50:
                logger.warning(f"  → Insufficient text extracted from {url}")
                continue

            items.append({
                "type": "article",
                "title": title,
                "url": url,
                "source_name": source_name,
                "source_tier": source_tier,
                "published_at": None,
                "text": text,
                "transcript": None,
                "content_length": len(text),
            })

            logger.info(f"  → Extracted: {title[:60]}...")

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching {url}: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            continue

    logger.info(f"Total web pages fetched: {len(items)}")
    return items
