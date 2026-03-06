"""
LLM Related Topics — suggests related health topics from
the taxonomy based on the current content item.
"""

import json
import logging
from backend.core.settings import load_prompt, get_topics
from backend.core.safety import validate_llm_json
from backend.llm.llm_manager import get_llm

logger = logging.getLogger(__name__)


def suggest_related_topics(
    title: str,
    current_tags: list[str],
    text: str = "",
) -> list[dict]:
    """
    Suggest 2-3 related topics from the taxonomy that a reader
    of this content might also want to explore.

    Args:
        title: Content item title
        current_tags: Currently assigned topic tags
        text: Content text (optional, for context)

    Returns:
        List of dicts: [{"topic": str, "reason": str}]
    """
    llm = get_llm()

    all_topics = get_topics()
    # Exclude current tags so we suggest NEW topics
    available_topics = [t for t in all_topics if t not in current_tags]

    if not available_topics:
        return []

    try:
        prompt_template = load_prompt("related_topics.txt")
    except FileNotFoundError:
        logger.error("Related topics prompt template not found")
        return []

    prompt = prompt_template.format(
        title=title,
        current_tags=", ".join(current_tags) if current_tags else "none",
        text_snippet=text[:500] if text else title,
        available_topics=", ".join(available_topics),
    )

    try:
        raw_output = llm.generate(prompt, temperature=0.2)
    except Exception as e:
        logger.error(f"LLM related topics generation failed: {e}")
        return []

    parsed = validate_llm_json(raw_output)
    if parsed is None:
        logger.warning("LLM returned invalid JSON for related topics")
        return []

    suggestions = parsed.get("related_topics", [])

    # Validate against taxonomy
    valid_set = set(available_topics)
    validated = []
    for item in suggestions[:3]:
        if isinstance(item, dict) and item.get("topic") in valid_set:
            validated.append({
                "topic": item["topic"],
                "reason": item.get("reason", "Related health topic"),
            })

    return validated
