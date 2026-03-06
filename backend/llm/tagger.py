"""
LLM Tagger — assigns topic tags to content items from the fixed taxonomy.
"""

import json
import logging
from backend.core.db import get_db
from backend.core.settings import load_prompt, get_topics
from backend.core.safety import validate_llm_json
from backend.core.schema import LLMTagOutput
from backend.core.utils import truncate_text
from backend.llm.ollama_client import get_ollama_client

logger = logging.getLogger(__name__)


def tag_content(title: str, text: str) -> list[str]:
    """
    Generate topic tags for a content item using the LLM.
    Tags are validated against the fixed taxonomy.
    """
    valid_topics = get_topics()
    topics_list = ", ".join(valid_topics)

    try:
        prompt_template = load_prompt("tag_item.txt")
    except FileNotFoundError:
        logger.error("Tag prompt template not found")
        return []

    prompt = prompt_template.format(
        title=title,
        text=truncate_text(text or title, max_length=1500),
        topics_list=topics_list,
    )

    client = get_ollama_client()
    try:
        raw_output = client.generate(prompt)
    except Exception as e:
        logger.error(f"LLM generation failed for tagging: {e}")
        return []

    parsed = validate_llm_json(raw_output)
    if parsed is None:
        logger.warning(f"LLM returned invalid JSON for tagging: {title}")
        return []

    try:
        validated = LLMTagOutput(**parsed)
        tags = validated.topic_tags
    except Exception:
        logger.warning(f"Tag output failed schema validation: {title}")
        return []

    # Filter to valid taxonomy only
    valid_set = set(valid_topics)
    filtered = [t for t in tags if t in valid_set]

    return filtered


def tag_untagged_items():
    """
    Find all content items without tags and generate them.
    """
    client = get_ollama_client()
    if not client.is_available():
        logger.warning("Ollama not available — skipping tagging")
        return

    with get_db() as conn:
        cursor = conn.execute(
            "SELECT id, title, text, transcript "
            "FROM content_items WHERE tags_json = '[]' OR tags_json IS NULL"
        )
        items = cursor.fetchall()

    if not items:
        logger.info("No items to tag")
        return

    logger.info(f"Tagging {len(items)} items...")

    for row in items:
        item = dict(row)
        content_text = item.get("text") or item.get("transcript") or ""

        logger.info(f"  Tagging: {item['title'][:50]}...")
        tags = tag_content(title=item["title"], text=content_text)

        if tags:
            with get_db() as conn:
                conn.execute(
                    "UPDATE content_items SET tags_json = ? WHERE id = ?",
                    (json.dumps(tags), item["id"]),
                )

    logger.info(f"Tagging complete: {len(items)} items processed")
