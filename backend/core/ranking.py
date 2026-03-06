"""
Content ranking module — deterministic scoring for personalized feed.
No LLM involved. Scoring is based on:
  - Topic match with family member interests
  - Age band relevance
  - Content format preference
  - Recency
  - Content length preference
"""

import json
from datetime import datetime, timezone


def score_content_for_member(item: dict, member: dict) -> float:
    """
    Score a content item for a specific family member.
    Returns a score ≥ 0. Higher = more relevant.
    """
    score = 0.0

    # Parse member data
    member_topics = _safe_json_list(member.get("topics_json", "[]"))
    prefs = _safe_json_dict(member.get("preferences_json", "{}"))
    age_band = member.get("age_band", "adult")

    # Parse item data
    item_tags = _safe_json_list(item.get("tags_json", "[]"))
    item_type = item.get("type", "article")
    content_length = item.get("content_length", 0)

    # ── Topic match (0-50 points) ──────────────────────────
    if member_topics and item_tags:
        matching = set(member_topics) & set(item_tags)
        if matching:
            score += min(len(matching) * 20, 50)

    # ── Age band relevance (0-15 points) ───────────────────
    age_topic_map = {
        "kid": ["child-health", "immunization", "nutrition"],
        "teen": ["mental-health", "nutrition", "exercise-fitness", "skin-conditions"],
        "adult": [],  # No specific boost — all topics relevant
        "senior": ["senior-health", "heart-health", "bone-joint", "diabetes"],
    }
    age_relevant = age_topic_map.get(age_band, [])
    if age_relevant and item_tags:
        age_match = set(age_relevant) & set(item_tags)
        if age_match:
            score += 15

    # ── Format preference (0-10 points) ────────────────────
    format_pref = prefs.get("content_format", "all")
    if format_pref == "video" and item_type == "video":
        score += 10
    elif format_pref == "text" and item_type == "article":
        score += 10
    elif format_pref == "all":
        score += 5  # Small baseline

    # ── Content length preference (0-10 points) ────────────
    length_pref = prefs.get("length_preference", "any")
    if length_pref == "short" and content_length < 2000:
        score += 10
    elif length_pref == "long" and content_length >= 2000:
        score += 10
    elif length_pref == "any":
        score += 5

    # ── Recency boost (0-15 points) ────────────────────────
    published = item.get("published_at")
    if published:
        try:
            pub_date = datetime.fromisoformat(published.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            days_old = (now - pub_date).days
            if days_old <= 7:
                score += 15
            elif days_old <= 30:
                score += 10
            elif days_old <= 90:
                score += 5
        except (ValueError, TypeError):
            pass

    return score


def rank_content_for_member(items: list[dict], member: dict) -> list[dict]:
    """
    Rank content items for a family member by relevance score.
    Returns items sorted by descending score.
    """
    scored = []
    for item in items:
        s = score_content_for_member(item, member)
        scored.append((s, item))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in scored]


def rank_content_for_group(items: list[dict], members: list[dict]) -> list[dict]:
    """
    Rank content for an entire family group by averaging scores
    across members.
    """
    if not members:
        return items

    item_scores: dict[int, float] = {}
    for item in items:
        total = sum(score_content_for_member(item, m) for m in members)
        item_scores[item["id"]] = total / len(members)

    items_sorted = sorted(items, key=lambda x: item_scores.get(x["id"], 0), reverse=True)
    return items_sorted


def _safe_json_list(val) -> list:
    if isinstance(val, list):
        return val
    if isinstance(val, str):
        try:
            result = json.loads(val)
            return result if isinstance(result, list) else []
        except (json.JSONDecodeError, TypeError):
            return []
    return []


def _safe_json_dict(val) -> dict:
    if isinstance(val, dict):
        return val
    if isinstance(val, str):
        try:
            result = json.loads(val)
            return result if isinstance(result, dict) else {}
        except (json.JSONDecodeError, TypeError):
            return {}
    return {}
