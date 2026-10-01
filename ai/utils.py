"""
Shared AI helpers (ai/utils.py).

generate_fitty_response(): single-prompt LLM call with tiered fallback
    Gemini (primary -> backup model)  ->  Groq  ->  friendly offline message
detect_query_intent(): lightweight keyword intent detection (English + Hindi)

Configuration (Backend/.env)
----------------------------
GEMINI_API_KEY, GEMINI_MODELS (default: gemini-3.8-flash,gemini-2.5-flash)
GROQ_API_KEY,   GROQ_MODELS   (default: llama-3.3-70b-versatile)
"""

import logging
import os
import re
from typing import List, Optional

from django.conf import settings

logger = logging.getLogger(__name__)

GROQ_TIMEOUT_SECONDS = 20
OFFLINE_MESSAGE = (
    "Fitty is currently doing some heavy lifting! 🏋️ "
    "Try again in a few seconds, Champ!"
)


def _env_list(name: str, default: str) -> List[str]:
    raw = os.getenv(name, default)
    return [item.strip() for item in raw.split(",") if item.strip()]


GEMINI_MODELS = _env_list("GEMINI_MODELS", "gemini-3.8-flash,gemini-2.5-flash")
GROQ_MODELS = _env_list("GROQ_MODELS", "llama-3.3-70b-versatile")


# --------------------------------------------------------------------------
# LLM providers
# --------------------------------------------------------------------------


def _call_gemini(prompt: str) -> Optional[str]:
    api_key = getattr(settings, "GEMINI_API_KEY", None) or os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.warning("GEMINI_API_KEY is not set; skipping Gemini.")
        return None

    try:
        from google import genai

        client = genai.Client(api_key=api_key)
    except Exception as exc:
        logger.warning("Gemini client could not be created: %s", exc)
        return None

    for model_name in GEMINI_MODELS:
        try:
            response = client.models.generate_content(
                model=model_name, contents=prompt
            )
            if response and response.text:
                return response.text
        except Exception as exc:
            logger.warning("Gemini model %s failed: %s", model_name, exc)
    return None


def _call_groq(prompt: str) -> Optional[str]:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        logger.warning("GROQ_API_KEY is not set; skipping Groq.")
        return None

    try:
        from groq import Groq

        client = Groq(api_key=api_key, timeout=GROQ_TIMEOUT_SECONDS)
    except Exception as exc:
        logger.warning("Groq client could not be created: %s", exc)
        return None

    for model_name in GROQ_MODELS:
        try:
            completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=model_name,
            )
            content = completion.choices[0].message.content
            if content:
                return content
        except Exception as exc:
            logger.warning("Groq model %s failed: %s", model_name, exc)
    return None


def generate_fitty_response(user_message: str) -> str:
    """Tiered reliability: Gemini -> Groq -> friendly offline message."""
    text = _call_gemini(user_message)
    if text:
        return text

    text = _call_groq(user_message)
    if text:
        logger.info("Reply served by Groq fallback.")
        return text

    logger.error("All AI providers failed in generate_fitty_response.")
    return OFFLINE_MESSAGE


# --------------------------------------------------------------------------
# Intent detection
# --------------------------------------------------------------------------

# Order matters: the first matching intent wins.
INTENT_KEYWORDS = {
    "pushup": ["pushup", "push up", "पुश"],
    "pullup": ["pullup", "pull up", "चिनअप", "पुल"],
    "squat": ["squat", "स्क्वाट", "बैठक"],
    "diet": ["diet", "food", "nutrition", "खाना", "आहार"],
    "weight_loss": ["weight loss", "fat loss", "reduce", "वजन", "मोटापा"],
    "muscle_gain": ["muscle", "gain", "build", "size", "मांसपेशी", "बनाना"],
    "cardio": ["cardio", "running", "cycling", "हृदय"],
    "form": ["form", "technique", "सही", "तरीका"],
    "program": ["program", "plan", "routine", "योजना", "कार्यक्रम"],
}


def _keyword_matches(query: str, keyword: str) -> bool:
    """
    English keywords match on word boundaries (so "gain" does not match
    "again"). Hindi keywords use plain substring matching, because word
    boundaries are unreliable for Devanagari.
    """
    if keyword.isascii():
        return re.search(rf"\b{re.escape(keyword)}", query) is not None
    return keyword in query


def detect_query_intent(query: str) -> str:
    """Detect what the user is asking about. Returns 'general' if no match."""
    query_lower = (query or "").lower()
    for intent, keywords in INTENT_KEYWORDS.items():
        if any(_keyword_matches(query_lower, kw) for kw in keywords):
            return intent
    return "general"