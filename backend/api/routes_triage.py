"""
Triage API routes — rule-based seek-care guidance.
100% deterministic — NO LLM involvement.
"""

from fastapi import APIRouter, HTTPException
from backend.core.settings import get_triage_rules, get_specialist_map
from backend.core.schema import (
    TriageRunRequest, TriageRunResponse,
    TriageQuestionsResponse, TriageQuestion,
)
from backend.core.safety import DISCLAIMER

router = APIRouter()


@router.get("/questions/{topic}", response_model=TriageQuestionsResponse)
def get_triage_questions(topic: str):
    """
    Get the triage questions for a given topic.
    Returns universal red-flag questions + topic-specific questions.
    """
    rules = get_triage_rules()

    # Universal questions
    universal_raw = rules.get("universal_red_flags", {}).get("questions", [])
    universal_qs = [
        TriageQuestion(id=q["id"], text=q["text"]) for q in universal_raw
    ]

    # Topic-specific questions
    topic_qs = []
    topic_rules = rules.get("topic_rules", [])
    matched = _find_topic_rule(topic_rules, topic)

    if matched:
        for q in matched.get("questions", []):
            topic_qs.append(TriageQuestion(id=q["id"], text=q["text"]))

    return TriageQuestionsResponse(
        topic=topic,
        universal_questions=universal_qs,
        topic_questions=topic_qs,
    )


@router.get("/topics")
def get_triage_topics():
    """List available triage topics."""
    rules = get_triage_rules()
    topics = [r["topic"] for r in rules.get("topic_rules", [])]
    return {
        "topics": topics,
        "disclaimer": DISCLAIMER,
    }


@router.post("/run", response_model=TriageRunResponse)
def run_triage(req: TriageRunRequest):
    """
    Run the triage assessment based on yes/no answers.
    This is 100% rule-based — no LLM involvement.

    Steps:
    1. Check universal red flags first
    2. Check topic-specific red flags
    3. Determine urgency level
    4. Attach specialist suggestion
    """
    rules = get_triage_rules()
    answers = req.answers  # {question_id: True/False}

    # ── Step 1: Check universal red flags ──────────────────
    universal = rules.get("universal_red_flags", {})
    universal_questions = universal.get("questions", [])
    universal_ids = [q["id"] for q in universal_questions]

    for uid in universal_ids:
        if answers.get(uid, False):
            # Any universal red flag → emergency
            output = universal.get("output", {})
            specialist = _get_specialist(req.topic)
            return TriageRunResponse(
                urgency=output.get("urgency", "emergency"),
                message=output.get("message", "Please seek immediate medical attention."),
                source_refs=output.get("source_refs", []),
                specialist=specialist,
            )

    # ── Step 2: Check topic-specific rules ─────────────────
    topic_rules_list = rules.get("topic_rules", [])
    matched = _find_topic_rule(topic_rules_list, req.topic)

    if not matched:
        # Fall back to general
        matched = _find_topic_rule(topic_rules_list, "general")

    if matched:
        red_flags = matched.get("red_flags", [])
        outputs = matched.get("outputs", {})
        topic_questions = matched.get("questions", [])
        topic_ids = [q["id"] for q in topic_questions]

        # Check if any red flag question was answered yes
        red_flag_hit = any(answers.get(rf, False) for rf in red_flags)

        if red_flag_hit and "red_flag_hit" in outputs:
            result = outputs["red_flag_hit"]
            specialist = _get_specialist(req.topic)
            return TriageRunResponse(
                urgency=result.get("urgency", "emergency"),
                message=result.get("message", ""),
                source_refs=result.get("source_refs", []),
                specialist=specialist,
            )

        # Check if any topic question was answered yes
        any_yes = any(answers.get(qid, False) for qid in topic_ids)

        if any_yes and "some_yes" in outputs:
            result = outputs["some_yes"]
            specialist = _get_specialist(req.topic)
            return TriageRunResponse(
                urgency=result.get("urgency", "soon"),
                message=result.get("message", ""),
                source_refs=result.get("source_refs", []),
                specialist=specialist,
            )

        # All no
        result = outputs.get("all_no", {})
        specialist = _get_specialist(req.topic)
        return TriageRunResponse(
            urgency=result.get("urgency", "routine"),
            message=result.get("message", "Routine monitoring may be appropriate."),
            source_refs=result.get("source_refs", []),
            specialist=specialist,
        )

    # No matching rule — default to routine
    specialist = _get_specialist(req.topic)
    return TriageRunResponse(
        urgency="routine",
        message="Based on your answers, consider discussing at your next regular check-up.",
        source_refs=[],
        specialist=specialist,
    )


def _find_topic_rule(rules_list: list, topic: str) -> dict | None:
    """Find the rule set for a given topic."""
    for rule in rules_list:
        if rule.get("topic") == topic:
            return rule
    return None


def _get_specialist(topic: str) -> dict:
    """Get specialist info for a topic from the specialist map."""
    spec_map = get_specialist_map()
    default_specialist = spec_map.get("default_specialist", "Primary Care Physician")
    mappings = spec_map.get("mappings", {})

    if topic in mappings:
        info = mappings[topic]
        return {
            "specialists": info.get("specialists", [default_specialist]),
            "note": info.get("note", f"This topic is commonly handled by a {default_specialist}."),
        }

    return {
        "specialists": [default_specialist],
        "note": f"Consider starting with a {default_specialist} for general guidance.",
    }
