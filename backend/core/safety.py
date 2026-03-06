"""
Safety module — banned phrase detection, LLM output validation,
refusal handling, and content neutralization.

This is a critical guardrail layer. ALL LLM output passes through
these filters before being stored or displayed.
"""

import json
import re
from backend.core.settings import load_prompt

# ── Banned Phrases ────────────────────────────────────────
# These patterns are checked case-insensitively against all
# system-generated text. If detected, the text is neutralized.
#
# NOTE: Context-aware patterns use negative lookbehind/lookahead
# to allow educational phrasing while blocking directive advice.

BANNED_PHRASES = [
    # Direct medical advice — always block
    r"\byou have [a-z]+",              # "you have diabetes"
    r"\byou likely have\b",
    r"\byou probably have\b",
    r"\byou might have\b",
    r"\byou may have\b",
    r"\byou should take\b",
    r"\byou should start\b",
    r"\byou should stop\b",
    r"\byou need to take\b",
    r"\bstart taking\b",
    r"\bstop taking\b",
    r"\bincrease your\b",
    r"\bdecrease your\b",
    r"\bdosage\b",
    r"\b\d+\s*mg\b",                   # Specific dosages
    r"\btreatment plan\b",
    r"\bmiracle cure\b",
    r"\bmiracle\b",
    r"\bguaranteed to\b",
    r"\bprescri(?:be|bed|ption)\b",
]

BANNED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in BANNED_PHRASES]

# Context-aware patterns — allowed in educational phrasing only
# These are checked separately and only flag when used in advice-giving context
CONTEXT_SENSITIVE_TERMS = {
    "diagnosis": {
        "block_patterns": [
            r"\byour diagnosis\b",
            r"\bdiagnosis is\b",
        ],
        "allow_patterns": [
            r"\b(discusses?|covers?|explains?|describes?|about)\b.*\bdiagnosis\b",
            r"\bdiagnosis\b.*\b(process|methods?|criteria|procedures?)\b",
            r"\bdiagnostic\b",
            r"\bearly diagnosis\b",
        ],
    },
    "cure": {
        "block_patterns": [
            r"\bthis will cure\b",
            r"\bcure for\b(?!.*\bno\b)",  # block "cure for X" unless preceded by "no"
        ],
        "allow_patterns": [
            r"\bno (known )?cure\b",
            r"\bcurrently no cure\b",
            r"\bthere is no cure\b",
            r"\bcure\b.*\b(research|development|trials?)\b",
        ],
    },
}

# Safe fallback summary when banned phrases are detected
SAFE_FALLBACK_SUMMARY = {
    "summary": "This content discusses a health-related topic from a verified source. Please visit the original source for full details.",
    "key_points": [
        "Content from a verified health source",
        "Covers a health-related topic",
        "Visit the original source for complete information"
    ],
    "warnings": ["Content was auto-summarized with a generic summary for safety."],
    "topic_tags": []
}


def contains_banned_phrases(text: str) -> bool:
    """Check if text contains any banned phrases."""
    if not text:
        return False
    for pattern in BANNED_PATTERNS:
        if pattern.search(text):
            return True
    # Check context-sensitive terms
    if _contains_context_violations(text):
        return True
    return False


def _contains_context_violations(text: str) -> bool:
    """
    Check context-sensitive terms. These are only flagged when
    used in directive/advice context, not educational context.
    """
    if not text:
        return False

    for term, rules in CONTEXT_SENSITIVE_TERMS.items():
        # Check if the term is even present
        if not re.search(rf"\b{term}\b", text, re.IGNORECASE):
            continue

        # Check if any allow pattern matches — if so, it's fine
        allowed = False
        for allow in rules["allow_patterns"]:
            if re.search(allow, text, re.IGNORECASE):
                allowed = True
                break

        if allowed:
            continue

        # Check if any block pattern matches
        for block in rules["block_patterns"]:
            if re.search(block, text, re.IGNORECASE):
                return True

    return False


def find_banned_phrases(text: str) -> list[str]:
    """Return all banned phrases found in text."""
    if not text:
        return []
    found = []
    for pattern in BANNED_PATTERNS:
        matches = pattern.findall(text)
        found.extend(matches)
    return found


def neutralize_summary(summary_dict: dict) -> dict:
    """
    Check a summary dict for banned phrases. If any are found,
    replace with safe fallback. Preserves topic_tags if valid.
    """
    text_to_check = json.dumps(summary_dict)
    if contains_banned_phrases(text_to_check):
        fallback = SAFE_FALLBACK_SUMMARY.copy()
        # Preserve valid topic tags if they exist
        if "topic_tags" in summary_dict and isinstance(summary_dict["topic_tags"], list):
            fallback["topic_tags"] = summary_dict["topic_tags"]
        return fallback
    return summary_dict


def validate_llm_json(raw_output: str) -> dict | None:
    """
    Parse and validate LLM JSON output. Returns dict or None if invalid.
    Attempts to extract JSON from markdown code blocks if present.
    """
    if not raw_output:
        return None

    text = raw_output.strip()

    # Try to extract from markdown code block
    json_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if json_match:
        text = json_match.group(1).strip()

    # Try to find JSON object
    brace_start = text.find("{")
    brace_end = text.rfind("}")
    if brace_start != -1 and brace_end != -1:
        text = text[brace_start:brace_end + 1]

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def is_advice_seeking(query: str) -> bool:
    """
    Check if a user query is seeking medical advice/diagnosis.
    Returns True if the query appears to be asking for advice.
    """
    advice_patterns = [
        r"\bwhat do i have\b",
        r"\bwhat('s| is) wrong with me\b",
        r"\bdo i have\b",
        r"\bshould i take\b",
        r"\bwhat medicine\b",
        r"\bwhat medication\b",
        r"\bhow to cure\b",
        r"\bam i sick\b",
        r"\bis it cancer\b",
        r"\bdiagnose me\b",
        r"\bwhat pill\b",
        r"\bprescri(?:be|ption)\b",
    ]
    if not query:
        return False
    for pattern in advice_patterns:
        if re.search(pattern, query, re.IGNORECASE):
            return True
    return False


def get_refusal_message() -> str:
    """Load the refusal message template."""
    try:
        return load_prompt("refusal_style.txt")
    except FileNotFoundError:
        return (
            "I cannot provide medical advice, diagnosis, or treatment recommendations. "
            "This system is for educational purposes only. "
            "Please consult a qualified healthcare professional for medical concerns. "
            "Educational content only. Not medical advice. If worried, seek professional care."
        )


DISCLAIMER = "Educational content only. Not medical advice. If worried, seek professional care."
