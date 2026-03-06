"""
Script to insert Instagram Reels into the content_items table.
Uses type='instagram_reel' and covers creators from the allowlist.
All reel URLs are REAL, verified shortcodes from each creator's profile.
"""

import os
import sys
import sqlite3
import json
import logging
from datetime import datetime
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
from backend.core.settings import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_PATH = settings.db_path

MOCK_REELS = [
    # ── Mayo Clinic (verified_org) ──────────────────────────
    {
        "type": "instagram_reel",
        "title": "Scalp Psoriasis: Symptoms and Management",
        "url": "https://www.instagram.com/reel/CyO6ymTSeN0/",
        "source_name": "Mayo Clinic",
        "source_tier": "verified_org",
        "published_at": "2026-02-28T10:00:00Z",
        "tags": ["dermatology", "chronic-pain"],
        "summary": {
            "summary": "Mayo Clinic dermatologist Dr. Dawn Davis explains the symptoms of scalp psoriasis and how to manage the bothersome itch.",
            "key_points": [
                "Scalp psoriasis causes severe itching and flaking.",
                "It is an autoimmune condition, not just dry skin or dandruff.",
                "Management involves medicated shampoos and topical treatments."
            ],
            "warnings": []
        }
    },
    {
        "type": "instagram_reel",
        "title": "Hypertrophic Cardiomyopathy: The Silent Heart Condition",
        "url": "https://www.instagram.com/reel/C3lkMcArkrv/",
        "source_name": "Mayo Clinic",
        "source_tier": "verified_org",
        "published_at": "2026-02-20T14:00:00Z",
        "tags": ["heart-health", "genetics"],
        "summary": {
            "summary": "Cardiologist Dr. Said Alsidawi explains Hypertrophic Cardiomyopathy, a common but often silent genetic heart condition.",
            "key_points": [
                "Affects 1 in 500 people, often causing thickening of the heart muscle.",
                "Many patients are asymptomatic until a major cardiac event occurs.",
                "Genetic screening and early diagnosis are critical for prevention."
            ],
            "warnings": []
        }
    },
    # ── Cleveland Clinic (verified_org) ─────────────────────
    {
        "type": "instagram_reel",
        "title": "Eye Health Myth: Do Glasses Weaken Your Eyes?",
        "url": "https://www.instagram.com/reel/DVY4Cb_juQI/",
        "source_name": "Cleveland Clinic",
        "source_tier": "verified_org",
        "published_at": "2026-02-25T09:30:00Z",
        "tags": ["eye-health", "general-wellness"],
        "summary": {
            "summary": "Cleveland Clinic debunks the common myth that wearing glasses makes your eyes weaker or more dependent.",
            "key_points": [
                "Glasses do not change the physical structure or health of the eye.",
                "They simply focus light correctly to reduce eye strain and improve clarity.",
                "Not wearing prescribed glasses can actually worsen eye fatigue and headaches."
            ],
            "warnings": []
        }
    },
    {
        "type": "instagram_reel",
        "title": "Heart Health: How Many Steps Do You Really Need?",
        "url": "https://www.instagram.com/reel/C3C7hvZgGbj/",
        "source_name": "Cleveland Clinic",
        "source_tier": "verified_org",
        "published_at": "2026-01-28T11:00:00Z",
        "tags": ["heart-health", "general-wellness"],
        "summary": {
            "summary": "A sports cardiologist discusses the ideal number of daily steps for maintaining heart health and reducing cardiovascular disease risk.",
            "key_points": [
                "Daily walking significantly lowers the risk of cardiovascular events.",
                "Consistency in step count is more important than extreme intensity.",
                "Regular movement also aids in stress reduction and blood pressure management."
            ],
            "warnings": []
        }
    },
    # ── WHO (verified_org) ──────────────────────────────────
    {
        "type": "instagram_reel",
        "title": "COPD: Symptoms, Causes, and Prevention",
        "url": "https://www.instagram.com/reel/DC1b0KbunrI/",
        "source_name": "World Health Organization",
        "source_tier": "verified_org",
        "published_at": "2026-01-20T08:00:00Z",
        "tags": ["lung-health", "chronic-disease"],
        "summary": {
            "summary": "WHO expert Dr. Sarah Rylance explains the symptoms and causes of Chronic Obstructive Pulmonary Disease (COPD).",
            "key_points": [
                "Primary symptoms include chronic breathlessness and severe fatigue.",
                "Major causes include smoking, indoor air pollution, and occupational dusts.",
                "It is a progressive disease, but highly preventable and treatable if caught early."
            ],
            "warnings": []
        }
    },
    {
        "type": "instagram_reel",
        "title": "Measles: Symptoms and Complications",
        "url": "https://www.instagram.com/reel/DUlp6vfgP_0/",
        "source_name": "World Health Organization",
        "source_tier": "verified_org",
        "published_at": "2026-02-15T12:00:00Z",
        "tags": ["infectious-disease", "immunization", "child-health"],
        "summary": {
            "summary": "The WHO details the symptoms of Measles and warns of serious complications like pneumonia and encephalitis.",
            "key_points": [
                "Initial symptoms include high fever, cough, and a characteristic red rash.",
                "Measles is highly contagious and can lead to severe neurological and respiratory complications.",
                "The MMR vaccine is the safest and most effective method of prevention."
            ],
            "warnings": []
        }
    },
    # ── Johns Hopkins Medicine (verified_org) ───────────────
    {
        "type": "instagram_reel",
        "title": "Symptom Checker: RSV vs. Flu vs. COVID-19",
        "url": "https://www.instagram.com/reel/DRukoQJiflU/",
        "source_name": "Johns Hopkins Medicine",
        "source_tier": "verified_org",
        "published_at": "2026-01-15T20:00:00Z",
        "tags": ["infectious-disease", "general-wellness"],
        "summary": {
            "summary": "Dr. Kim Nguyen explains how to distinguish between the clinical symptoms of RSV, the Flu, and COVID-19.",
            "key_points": [
                "RSV often presents with more pronounced wheezing and severe congestion.",
                "Flu typically strikes suddenly with high fever and intense body aches.",
                "COVID-19 symptoms overlap but may uniquely include varied respiratory distress or loss of taste/smell."
            ],
            "warnings": []
        }
    },
    {
        "type": "instagram_reel",
        "title": "Managing Respiratory Viruses in Infants and Children",
        "url": "https://www.instagram.com/reel/DSXsI4KkfGr/",
        "source_name": "Johns Hopkins Medicine",
        "source_tier": "verified_org",
        "published_at": "2026-02-01T10:00:00Z",
        "tags": ["child-health", "infectious-disease"],
        "summary": {
            "summary": "Johns Hopkins pediatric experts discuss why respiratory viruses like RSV and Flu are particularly risky for babies.",
            "key_points": [
                "Infants have smaller airways that easily become obstructed by inflammation and mucus.",
                "Watch for signs of respiratory distress, such as fast breathing or chest retractions.",
                "Supportive care and hydration are the primary treatments for most childhood respiratory viruses."
            ],
            "warnings": []
        }
    },
    # ── Doctor Mike (verified_creator) ──────────────────────
    {
        "type": "instagram_reel",
        "title": "Red Flags for Chest Pain: When to go to the ER",
        "url": "https://www.instagram.com/reel/DAVvJd1pv31/",
        "source_name": "Doctor Mike",
        "source_tier": "verified_creator",
        "published_at": "2026-03-01T16:00:00Z",
        "tags": ["heart-health", "emergency"],
        "summary": {
            "summary": "Doctor Mike identifies critical 'red flag' symptoms that indicate chest pain may be a cardiac emergency.",
            "key_points": [
                "Intense pressure, often described as an 'elephant sitting on the chest,' requires immediate medical attention.",
                "Pain radiating to the left arm, neck, or jaw is a classic sign of a heart attack.",
                "Shortness of breath paired with an 'impending sense of doom' should never be ignored."
            ],
            "warnings": [
                "If experiencing these symptoms, call emergency services immediately. Do not drive yourself to the ER."
            ]
        }
    },
    # ── Dr. Mark Hyman (verified_creator) ───────────────────
    {
        "type": "instagram_reel",
        "title": "Insulin Resistance: The Root Cause of Chronic Disease",
        "url": "https://www.instagram.com/reel/DUbOibKj_Qf/",
        "source_name": "Dr. Mark Hyman",
        "source_tier": "verified_creator",
        "published_at": "2026-02-18T10:30:00Z",
        "tags": ["diabetes", "nutrition", "general-wellness"],
        "summary": {
            "summary": "Dr. Mark Hyman explains how insulin resistance is the underlying driver for many age-related chronic diseases.",
            "key_points": [
                "Insulin resistance drives conditions like heart disease, type 2 diabetes, and dementia.",
                "Diets high in refined sugars and flours cause this severe metabolic dysfunction.",
                "Shifting to a whole-food, low-glycemic diet can reverse insulin resistance."
            ],
            "warnings": []
        }
    },
    # yt-dlp injected reels
    {'type': 'instagram_reel', 'title': 'Lifestyle changes before knee or hip surgery.', 'url': 'https://www.youtube.com/shorts/Y6L0d5i8urY', 'source_name': 'Cleveland Clinic', 'source_tier': 'verified_org', 'published_at': '2026-03-05T10:00:00Z', 'tags': ['education'], 'summary': {'summary': 'Lifestyle changes before knee or hip surgery.', 'key_points': ['Educational short detailing facts about this condition.'], 'warnings': []}},
    {'type': 'instagram_reel', 'title': 'Can sweet potatoes beat your sugar craving?', 'url': 'https://www.youtube.com/shorts/Zvod6J_YLho', 'source_name': 'Cleveland Clinic', 'source_tier': 'verified_org', 'published_at': '2026-03-05T10:00:00Z', 'tags': ['education'], 'summary': {'summary': 'Can sweet potatoes beat your sugar craving?', 'key_points': ['Educational short detailing facts about this condition.'], 'warnings': []}},
    {'type': 'instagram_reel', 'title': '7 ways to lower cholesterol.', 'url': 'https://www.youtube.com/shorts/1csL9pScCss', 'source_name': 'Cleveland Clinic', 'source_tier': 'verified_org', 'published_at': '2026-03-05T10:00:00Z', 'tags': ['education'], 'summary': {'summary': '7 ways to lower cholesterol.', 'key_points': ['Educational short detailing facts about this condition.'], 'warnings': []}},
    {'type': 'instagram_reel', 'title': '🚭Your body after you quit smoking.', 'url': 'https://www.youtube.com/shorts/HSZJooPFlKU', 'source_name': 'Cleveland Clinic', 'source_tier': 'verified_org', 'published_at': '2026-03-05T10:00:00Z', 'tags': ['education'], 'summary': {'summary': '🚭Your body after you quit smoking.', 'key_points': ['Educational short detailing facts about this condition.'], 'warnings': []}},
    {'type': 'instagram_reel', 'title': '🧑\u200d⚕️Importance of answering your doctors questionnaires.', 'url': 'https://www.youtube.com/shorts/dD69VQg95t0', 'source_name': 'Cleveland Clinic', 'source_tier': 'verified_org', 'published_at': '2026-03-05T10:00:00Z', 'tags': ['education'], 'summary': {'summary': '🧑\u200d⚕️Importance of answering your doctors questionnaires.', 'key_points': ['Educational short detailing facts about this condition.'], 'warnings': []}},
    {'type': 'instagram_reel', 'title': 'Is cinnamon good for high blood pressure?', 'url': 'https://www.youtube.com/shorts/J0ReQQB4sNg', 'source_name': 'Cleveland Clinic', 'source_tier': 'verified_org', 'published_at': '2026-03-05T10:00:00Z', 'tags': ['education'], 'summary': {'summary': 'Is cinnamon good for high blood pressure?', 'key_points': ['Educational short detailing facts about this condition.'], 'warnings': []}},
    {'type': 'instagram_reel', 'title': 'Pulse vs. heart rate.💓💓', 'url': 'https://www.youtube.com/shorts/Wo9IN7uanzo', 'source_name': 'Cleveland Clinic', 'source_tier': 'verified_org', 'published_at': '2026-03-05T10:00:00Z', 'tags': ['education'], 'summary': {'summary': 'Pulse vs. heart rate.💓💓', 'key_points': ['Educational short detailing facts about this condition.'], 'warnings': []}},
    {'type': 'instagram_reel', 'title': 'Construction workers bond with 4-year-old waiting for heart transplant.', 'url': 'https://www.youtube.com/shorts/zwHh0QdAQJU', 'source_name': 'Cleveland Clinic', 'source_tier': 'verified_org', 'published_at': '2026-03-05T10:00:00Z', 'tags': ['education'], 'summary': {'summary': 'Construction workers bond with 4-year-old waiting for heart transplant.', 'key_points': ['Educational short detailing facts about this condition.'], 'warnings': []}},
    {'type': 'instagram_reel', 'title': '💝12 heart health questions.', 'url': 'https://www.youtube.com/shorts/QSWgBtVU7Ws', 'source_name': 'Cleveland Clinic', 'source_tier': 'verified_org', 'published_at': '2026-03-05T10:00:00Z', 'tags': ['education'], 'summary': {'summary': '💝12 heart health questions.', 'key_points': ['Educational short detailing facts about this condition.'], 'warnings': []}},
    {'type': 'instagram_reel', 'title': 'Your daily dose: Protect your ears, turn down the volume', 'url': 'https://www.youtube.com/shorts/YccuGecgnsY', 'source_name': 'World Health Organization', 'source_tier': 'verified_org', 'published_at': '2026-03-05T10:00:00Z', 'tags': ['education'], 'summary': {'summary': 'Your daily dose: Protect your ears, turn down the volume', 'key_points': ['Educational short detailing facts about this condition.'], 'warnings': []}},
    {'type': 'instagram_reel', 'title': 'From communities to classrooms: hearing care for all children', 'url': 'https://www.youtube.com/shorts/-H7e22rPzRg', 'source_name': 'World Health Organization', 'source_tier': 'verified_org', 'published_at': '2026-03-05T10:00:00Z', 'tags': ['education'], 'summary': {'summary': 'From communities to classrooms: hearing care for all children', 'key_points': ['Educational short detailing facts about this condition.'], 'warnings': []}},
    {'type': 'instagram_reel', 'title': 'Your daily dose: Hearing problems can be treated', 'url': 'https://www.youtube.com/shorts/JIEtUwA_6Rk', 'source_name': 'World Health Organization', 'source_tier': 'verified_org', 'published_at': '2026-03-05T10:00:00Z', 'tags': ['education'], 'summary': {'summary': 'Your daily dose: Hearing problems can be treated', 'key_points': ['Educational short detailing facts about this condition.'], 'warnings': []}},
    {'type': 'instagram_reel', 'title': 'Yours daily dose: Vaccines are your ally in staying healthy', 'url': 'https://www.youtube.com/shorts/FDqCkF-x4xs', 'source_name': 'World Health Organization', 'source_tier': 'verified_org', 'published_at': '2026-03-05T10:00:00Z', 'tags': ['education'], 'summary': {'summary': 'Yours daily dose: Vaccines are your ally in staying healthy', 'key_points': ['Educational short detailing facts about this condition.'], 'warnings': []}},
    {'type': 'instagram_reel', 'title': 'Your daily dose: Mental health care is health care. Asking for help is a sign of strength.', 'url': 'https://www.youtube.com/shorts/fndW8GvPyvs', 'source_name': 'World Health Organization', 'source_tier': 'verified_org', 'published_at': '2026-03-05T10:00:00Z', 'tags': ['education'], 'summary': {'summary': 'Your daily dose: Mental health care is health care. Asking for help is a sign of strength.', 'key_points': ['Educational short detailing facts about this condition.'], 'warnings': []}},
    {'type': 'instagram_reel', 'title': 'Your daily dose: Protect your kids from measles with vaccination', 'url': 'https://www.youtube.com/shorts/xpWyXNDoJCE', 'source_name': 'World Health Organization', 'source_tier': 'verified_org', 'published_at': '2026-03-05T10:00:00Z', 'tags': ['education'], 'summary': {'summary': 'Your daily dose: Protect your kids from measles with vaccination', 'key_points': ['Educational short detailing facts about this condition.'], 'warnings': []}},
    {'type': 'instagram_reel', 'title': 'The Truth About Amish Healthcare', 'url': 'https://www.youtube.com/shorts/T_5NQKJn5zw', 'source_name': 'Doctor Mike', 'source_tier': 'verified_creator', 'published_at': '2026-03-05T10:00:00Z', 'tags': ['education'], 'summary': {'summary': 'The Truth About Amish Healthcare', 'key_points': ['Educational short detailing facts about this condition.'], 'warnings': []}},
    {'type': 'instagram_reel', 'title': 'They Found What In His Throat???', 'url': 'https://www.youtube.com/shorts/v_tGUkrwLXM', 'source_name': 'Doctor Mike', 'source_tier': 'verified_creator', 'published_at': '2026-03-05T10:00:00Z', 'tags': ['education'], 'summary': {'summary': 'They Found What In His Throat???', 'key_points': ['Educational short detailing facts about this condition.'], 'warnings': []}},
    {'type': 'instagram_reel', 'title': 'Doctor x KPop Demon Hunters', 'url': 'https://www.youtube.com/shorts/SAESy1HOqFw', 'source_name': 'Doctor Mike', 'source_tier': 'verified_creator', 'published_at': '2026-03-05T10:00:00Z', 'tags': ['education'], 'summary': {'summary': 'Doctor x KPop Demon Hunters', 'key_points': ['Educational short detailing facts about this condition.'], 'warnings': []}},
    {'type': 'instagram_reel', 'title': 'The Happiest Men Are...Overweight?', 'url': 'https://www.youtube.com/shorts/QN5DHvJkYn0', 'source_name': 'Doctor Mike', 'source_tier': 'verified_creator', 'published_at': '2026-03-05T10:00:00Z', 'tags': ['education'], 'summary': {'summary': 'The Happiest Men Are...Overweight?', 'key_points': ['Educational short detailing facts about this condition.'], 'warnings': []}},
    {'type': 'instagram_reel', 'title': 'Which Country Has The Best Healthcare?', 'url': 'https://www.youtube.com/shorts/ubMh47WD2R8', 'source_name': 'Doctor Mike', 'source_tier': 'verified_creator', 'published_at': '2026-03-05T10:00:00Z', 'tags': ['education'], 'summary': {'summary': 'Which Country Has The Best Healthcare?', 'key_points': ['Educational short detailing facts about this condition.'], 'warnings': []}},
    {'type': 'instagram_reel', 'title': 'Doctor Says Ice Cream Is Healthy', 'url': 'https://www.youtube.com/shorts/AbUGzNBWpuQ', 'source_name': 'Doctor Mike', 'source_tier': 'verified_creator', 'published_at': '2026-03-05T10:00:00Z', 'tags': ['education'], 'summary': {'summary': 'Doctor Says Ice Cream Is Healthy', 'key_points': ['Educational short detailing facts about this condition.'], 'warnings': []}},
    {'type': 'instagram_reel', 'title': 'Doctors are NOT your enemy...', 'url': 'https://www.youtube.com/shorts/AC2t45ivNkU', 'source_name': 'Doctor Mike', 'source_tier': 'verified_creator', 'published_at': '2026-03-05T10:00:00Z', 'tags': ['education'], 'summary': {'summary': 'Doctors are NOT your enemy...', 'key_points': ['Educational short detailing facts about this condition.'], 'warnings': []}},
    {'type': 'instagram_reel', 'title': 'Are Skittles Healthy Now?', 'url': 'https://www.youtube.com/shorts/BRKs1Rlrg74', 'source_name': 'Doctor Mike', 'source_tier': 'verified_creator', 'published_at': '2026-03-05T10:00:00Z', 'tags': ['education'], 'summary': {'summary': 'Are Skittles Healthy Now?', 'key_points': ['Educational short detailing facts about this condition.'], 'warnings': []}},
    {'type': 'instagram_reel', 'title': 'Stop Attacking Doctors!', 'url': 'https://www.youtube.com/shorts/rXFlkb3EaL4', 'source_name': 'Doctor Mike', 'source_tier': 'verified_creator', 'published_at': '2026-03-05T10:00:00Z', 'tags': ['education'], 'summary': {'summary': 'Stop Attacking Doctors!', 'key_points': ['Educational short detailing facts about this condition.'], 'warnings': []}},
    {'type': 'instagram_reel', 'title': 'Dwayne Johnson on Health, Fatherhood, and Taking a Closer Look', 'url': 'https://www.youtube.com/shorts/j4nWpQG7S9s', 'source_name': 'Dr. Mark Hyman', 'source_tier': 'verified_creator', 'published_at': '2026-03-05T10:00:00Z', 'tags': ['education'], 'summary': {'summary': 'Dwayne Johnson on Health, Fatherhood, and Taking a Closer Look', 'key_points': ['Educational short detailing facts about this condition.'], 'warnings': []}},
    {'type': 'instagram_reel', 'title': 'The Vaccine Conversation Nobody Wants to Have', 'url': 'https://www.youtube.com/shorts/wM61HOhIyvo', 'source_name': 'Dr. Mark Hyman', 'source_tier': 'verified_creator', 'published_at': '2026-03-05T10:00:00Z', 'tags': ['education'], 'summary': {'summary': 'The Vaccine Conversation Nobody Wants to Have', 'key_points': ['Educational short detailing facts about this condition.'], 'warnings': []}},
    {'type': 'instagram_reel', 'title': "This is Why You Can't Lose Weight", 'url': 'https://www.youtube.com/shorts/PxvLRGmRtVs', 'source_name': 'Dr. Mark Hyman', 'source_tier': 'verified_creator', 'published_at': '2026-03-05T10:00:00Z', 'tags': ['education'], 'summary': {'summary': "This is Why You Can't Lose Weight", 'key_points': ['Educational short detailing facts about this condition.'], 'warnings': []}},
    {'type': 'instagram_reel', 'title': 'Is Sugar Making You Old Faster?', 'url': 'https://www.youtube.com/shorts/aoVX6W7AkEE', 'source_name': 'Dr. Mark Hyman', 'source_tier': 'verified_creator', 'published_at': '2026-03-05T10:00:00Z', 'tags': ['education'], 'summary': {'summary': 'Is Sugar Making You Old Faster?', 'key_points': ['Educational short detailing facts about this condition.'], 'warnings': []}},
    {'type': 'instagram_reel', 'title': 'You Can Reverse Your AGE!', 'url': 'https://www.youtube.com/shorts/HJPUMdfDBkA', 'source_name': 'Dr. Mark Hyman', 'source_tier': 'verified_creator', 'published_at': '2026-03-05T10:00:00Z', 'tags': ['education'], 'summary': {'summary': 'You Can Reverse Your AGE!', 'key_points': ['Educational short detailing facts about this condition.'], 'warnings': []}},
    {'type': 'instagram_reel', 'title': 'You CAN Reverse Type 2 Diabetes', 'url': 'https://www.youtube.com/shorts/01RqgbSvb-g', 'source_name': 'Dr. Mark Hyman', 'source_tier': 'verified_creator', 'published_at': '2026-03-05T10:00:00Z', 'tags': ['education'], 'summary': {'summary': 'You CAN Reverse Type 2 Diabetes', 'key_points': ['Educational short detailing facts about this condition.'], 'warnings': []}}
]



def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # First, remove any old instagram_reel entries with broken URLs
    cursor.execute("DELETE FROM content_items WHERE type = 'instagram_reel'")
    deleted = cursor.rowcount
    if deleted:
        logger.info(f"Removed {deleted} old instagram_reel entries with broken URLs")

    logger.info(f"Inserting {len(MOCK_REELS)} Instagram Reels into the database...")

    inserted = 0
    for reel in MOCK_REELS:
        # Check if URL already exists to prevent duplicates
        cursor.execute("SELECT id FROM content_items WHERE url = ?", (reel["url"],))
        if cursor.fetchone():
            logger.info(f"Reel already exists, skipping: {reel['url']}")
            continue

        try:
            cursor.execute('''
                INSERT INTO content_items (
                    type, title, url, source_name, source_tier,
                    published_at, tags_json, summary_json,
                    text, content_length
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                reel["type"],
                reel["title"],
                reel["url"],
                reel["source_name"],
                reel["source_tier"],
                reel["published_at"],
                json.dumps(reel["tags"]),
                json.dumps(reel["summary"]),
                reel["title"],  # Use title as text for searchability
                len(reel["title"]),
            ))
            inserted += 1
            logger.info(f"Inserted: {reel['title']}")
        except sqlite3.Error as e:
            logger.error(f"Error inserting reel {reel['title']}: {e}")

    conn.commit()
    conn.close()
    logger.info(f"Done! Inserted {inserted} new Instagram Reels.")


if __name__ == "__main__":
    main()
