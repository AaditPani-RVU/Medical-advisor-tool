"""
LLM Content Q&A — answers user questions grounded ONLY in the
article's source text. No external knowledge.
"""

import logging
from backend.core.settings import load_prompt
from backend.core.safety import contains_banned_phrases, DISCLAIMER
from backend.core.utils import truncate_text
from backend.llm.llm_manager import get_llm

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are an educational health content assistant. You answer questions "
    "ONLY based on the provided source text. You never provide medical advice, "
    "diagnosis, or treatment recommendations. If the source text does not "
    "cover the user's question, say so honestly. Always remind the user "
    "that this is educational content, not medical advice."
)


def answer_question(
    question: str,
    title: str,
    source_name: str,
    text: str,
) -> dict:
    """
    Answer a user question about a specific content item.
    The answer is grounded ONLY in the provided text.

    Returns:
        {
            "answer": str,
            "grounded": bool,       # True if answered from text
            "source_title": str,
            "source_name": str,
            "disclaimer": str,
        }
    """
    llm = get_llm()

    try:
        prompt_template = load_prompt("content_qa.txt")
    except FileNotFoundError:
        logger.error("Content Q&A prompt template not found")
        return {
            "answer": "Q&A feature is not configured properly.",
            "grounded": False,
            "source_title": title,
            "source_name": source_name,
            "disclaimer": DISCLAIMER,
        }

    prompt = prompt_template.format(
        title=title,
        source_name=source_name,
        text=truncate_text(text, max_length=2500),
        question=question,
    )

    try:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        answer = llm.chat(messages, temperature=0.2)
    except Exception as e:
        logger.error(f"LLM Q&A generation failed: {e}")
        return {
            "answer": "Unable to generate an answer at this time.",
            "grounded": False,
            "source_title": title,
            "source_name": source_name,
            "disclaimer": DISCLAIMER,
        }

    # Safety check on output
    if contains_banned_phrases(answer):
        answer = (
            "I can provide educational information about this topic based on "
            f"the article from {source_name}. However, for specific medical "
            "questions, please consult a healthcare professional."
        )

    grounded = "not covered" not in answer.lower() and "not mentioned" not in answer.lower()

    return {
        "answer": answer,
        "grounded": grounded,
        "source_title": title,
        "source_name": source_name,
        "disclaimer": DISCLAIMER,
    }
