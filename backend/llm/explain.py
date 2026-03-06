"""
LLM Explain — rewrites content summaries at different reading levels.
Grounded in source text, no invented information.
"""

import logging
from backend.core.settings import load_prompt
from backend.core.utils import truncate_text
from backend.llm.llm_manager import get_llm

logger = logging.getLogger(__name__)

VALID_LEVELS = {"simple", "standard", "detailed"}

LEVEL_DESCRIPTIONS = {
    "simple": "for a young reader or someone unfamiliar with medical terms — use plain language, short sentences, and everyday analogies",
    "standard": "for a general adult audience — clear and informative with brief medical terms explained",
    "detailed": "for someone wanting in-depth understanding — include medical terminology with explanations, mechanisms, and nuances",
}


def explain_content(
    title: str,
    source_name: str,
    text: str,
    summary: str,
    level: str = "standard",
) -> dict:
    """
    Rewrite a content summary at the specified reading level.

    Args:
        title: Article title
        source_name: Source organization name
        text: Full article text
        summary: Existing summary
        level: One of "simple", "standard", "detailed"

    Returns:
        {
            "explanation": str,
            "level": str,
            "source_title": str,
            "disclaimer": str,
        }
    """
    if level not in VALID_LEVELS:
        level = "standard"

    llm = get_llm()

    try:
        prompt_template = load_prompt("explain_content.txt")
    except FileNotFoundError:
        logger.error("Explain prompt template not found")
        return {
            "explanation": summary or "Explain feature is not configured.",
            "level": level,
            "source_title": title,
            "disclaimer": DISCLAIMER,
        }

    level_desc = LEVEL_DESCRIPTIONS.get(level, LEVEL_DESCRIPTIONS["standard"])

    prompt = prompt_template.format(
        title=title,
        source_name=source_name,
        text=truncate_text(text or summary, max_length=2000),
        summary=summary or "No existing summary available.",
        level=level,
        level_description=level_desc,
    )

    try:
        explanation = llm.generate(
            prompt,
            temperature=0.3,
            system_prompt=(
                "You are an educational health content writer. Rewrite "
                "health content at different reading levels. Stay factual "
                "and grounded in the source material. Never provide "
                "medical advice."
            ),
        )
    except Exception as e:
        logger.error(f"LLM explain generation failed: {e}")
        return {
            "explanation": summary or "Unable to generate explanation.",
            "level": level,
            "source_title": title,
            "disclaimer": DISCLAIMER,
        }

    # Safety check
    if contains_banned_phrases(explanation):
        explanation = summary or (
            f"This article from {source_name} covers a health-related topic. "
            "Visit the original source for details."
        )

    return {
        "explanation": explanation,
        "level": level,
        "source_title": title,
        "disclaimer": DISCLAIMER,
    }
