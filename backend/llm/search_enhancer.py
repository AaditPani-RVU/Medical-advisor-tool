"""
LLM Search Enhancer — expands user search queries to related
medical terms for better content matching.
"""

import json
import logging
from backend.core.settings import load_prompt, get_topics
from backend.core.safety import validate_llm_json
from backend.llm.llm_manager import get_llm

logger = logging.getLogger(__name__)


def expand_search_query(query: str) -> dict:
    """
    Use the LLM to expand a search query into related medical terms
    and matching topic tags from our taxonomy.

    Args:
        query: The user's search query (e.g., "sugar problems")

    Returns:
        {
            "original_query": str,
            "expanded_terms": [str],  # related search terms
            "matched_topics": [str],  # matching topic tags from taxonomy
        }
    """
    llm = get_llm()

    topics_list = ", ".join(get_topics())

    try:
        prompt_template = load_prompt("expand_search.txt")
    except FileNotFoundError:
        logger.error("Search expansion prompt template not found")
        return {
            "original_query": query,
            "expanded_terms": [],
            "matched_topics": [],
        }

    prompt = prompt_template.format(
        query=query,
        topics_list=topics_list,
    )

    try:
        raw_output = llm.generate(prompt, temperature=0.1, max_tokens=512)
    except Exception as e:
        logger.error(f"LLM search expansion failed: {e}")
        return {
            "original_query": query,
            "expanded_terms": [],
            "matched_topics": [],
        }

    parsed = validate_llm_json(raw_output)
    if parsed is None:
        logger.warning(f"LLM returned invalid JSON for search expansion: {query}")
        return {
            "original_query": query,
            "expanded_terms": [],
            "matched_topics": [],
        }

    # Validate topic tags against taxonomy
    valid_topics = set(get_topics())
    matched_topics = [
        t for t in parsed.get("matched_topics", [])
        if t in valid_topics
    ]

    return {
        "original_query": query,
        "expanded_terms": parsed.get("expanded_terms", [])[:10],
        "matched_topics": matched_topics[:5],
    }
