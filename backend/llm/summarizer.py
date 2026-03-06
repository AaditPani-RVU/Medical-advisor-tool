"""
LLM Summarizer — generates neutral summaries for content items.
All output passes through the safety filter before storage.
"""

import json
import logging
from backend.core.db import get_db
from backend.core.settings import load_prompt, get_topics
from backend.core.safety import validate_llm_json, neutralize_summary, SAFE_FALLBACK_SUMMARY
from backend.core.schema import LLMSummaryOutput
from backend.core.utils import truncate_text
from backend.llm.ollama_client import get_ollama_client

logger = logging.getLogger(__name__)


def summarize_content(title: str, source_name: str, text: str) -> dict:
    """
    Generate a neutral summary for a content item using the LLM.
    Returns a validated, safety-filtered summary dict.
    """
    if not text and not title:
        return SAFE_FALLBACK_SUMMARY.copy()

    topics_list = ", ".join(get_topics())

    # Load and fill prompt template
    try:
        prompt_template = load_prompt("summarize_item.txt")
    except FileNotFoundError:
        logger.error("Summarize prompt template not found")
        return SAFE_FALLBACK_SUMMARY.copy()

    prompt = prompt_template.format(
        title=title,
        source_name=source_name,
        text=truncate_text(text or title, max_length=2000),
        topics_list=topics_list,
    )

    # Call LLM
    client = get_ollama_client()
    try:
        raw_output = client.generate(prompt)
    except Exception as e:
        logger.error(f"LLM generation failed: {e}")
        return SAFE_FALLBACK_SUMMARY.copy()

    # Parse JSON
    parsed = validate_llm_json(raw_output)
    if parsed is None:
        logger.warning(f"LLM returned invalid JSON for: {title}")
        return SAFE_FALLBACK_SUMMARY.copy()

    # Validate schema
    try:
        validated = LLMSummaryOutput(**parsed)
        summary_dict = validated.model_dump()
    except Exception:
        logger.warning(f"LLM output failed schema validation for: {title}")
        return SAFE_FALLBACK_SUMMARY.copy()

    # Validate topic tags against taxonomy
    valid_topics = set(get_topics())
    summary_dict["topic_tags"] = [
        t for t in summary_dict.get("topic_tags", [])
        if t in valid_topics
    ]

    # Safety filter — neutralize if banned phrases found
    summary_dict = neutralize_summary(summary_dict)

    return summary_dict


def summarize_unsummarized_items():
    """
    Find all content items without summaries and generate them.
    """
    client = get_ollama_client()
    if not client.is_available():
        logger.warning("Ollama not available — skipping summarization")
        return

    with get_db() as conn:
        cursor = conn.execute(
            "SELECT id, title, source_name, text, transcript "
            "FROM content_items WHERE summary_json = '{}' OR summary_json IS NULL"
        )
        items = cursor.fetchall()

    if not items:
        logger.info("No items to summarize")
        return

    logger.info(f"Summarizing {len(items)} items...")

    for row in items:
        item = dict(row)
        content_text = item.get("text") or item.get("transcript") or ""

        logger.info(f"  Summarizing: {item['title'][:50]}...")
        summary = summarize_content(
            title=item["title"],
            source_name=item["source_name"],
            text=content_text,
        )

        # Update DB
        with get_db() as conn:
            conn.execute(
                "UPDATE content_items SET summary_json = ? WHERE id = ?",
                (json.dumps(summary), item["id"]),
            )

    logger.info(f"Summarization complete: {len(items)} items processed")
