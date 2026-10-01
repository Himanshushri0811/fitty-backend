"""
Fitty AI - request router and response generator.

Flow
----
1. Fast path for plain greetings (no LLM call).
2. Keyword-based routing: relevant tools (workout / diet generator) are run
   in Python and their output is added to the prompt as context.
3. One LLM call with tiered fallback:
       Gemini (primary -> backup model)  ->  Groq  ->  offline canned reply

Configuration (Backend/.env)
----------------------------
GEMINI_API_KEY   required for Tier 1
GEMINI_MODELS    comma separated, tried in order  (default: gemini-3.8-flash,gemini-2.5-flash)
GROQ_API_KEY     required for Tier 2
GROQ_MODELS      comma separated, tried in order  (default: llama-3.3-70b-versatile)

Model names change often, so they live in .env and not in code.
"""

import logging
import os
import re
from typing import List, Optional, Tuple

from accounts.models import User

from .tools import diet_generator, generate_plan_pdf, workout_generator

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------


def _env_list(name: str, default: str) -> List[str]:
    """Read a comma separated env var into a clean list."""
    raw = os.getenv(name, default)
    return [item.strip() for item in raw.split(",") if item.strip()]


GEMINI_MODELS = _env_list("GEMINI_MODELS", "gemini-3.8-flash,gemini-2.5-flash")
GROQ_MODELS = _env_list("GROQ_MODELS", "llama-3.3-70b-versatile")

GROQ_TIMEOUT_SECONDS = 20
HISTORY_MESSAGES = 10  # last 10 messages = 5 user/assistant pairs

SOURCE_GEMINI = "gemini"
SOURCE_GROQ = "groq"
SOURCE_FALLBACK = "fallback"

GREETINGS = {
    "hi", "hello", "hey", "namaste", "what's up", "whats up",
    "hello fitty", "hi fitty", "hey fitty",
}

DIET_KEYWORDS = ["diet", "food", "eat", "meal", "nutrition", "calories", "protein"]
WORKOUT_KEYWORDS = [
    "workout", "exercise", "plan", "gym", "train",
    "chest", "legs", "gain", "loss",
]

# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------


def _contains(message: str, keywords: List[str]) -> bool:
    """
    Keyword match that avoids false positives.
    Short words (<= 3 chars) must match a whole word, so "hi" does not
    match "this" or "which". Longer words match as substrings
    ("workout" matches "workouts").
    """
    tokens = set(re.findall(r"[a-z']+", message.lower()))
    for keyword in keywords:
        if len(keyword) <= 3:
            if keyword in tokens:
                return True
        elif keyword in message.lower():
            return True
    return False


def get_smart_fallback(message: str) -> str:
    """Offline reply used only when every AI provider has failed."""
    if _contains(message, ["water", "hydrate", "drink"]):
        return (
            "Bhai, hydration is key! 💧 Aim for 3-4 liters daily. "
            "Carry a bottle everywhere to stay on track. 🔥"
        )
    if _contains(message, ["posture", "back", "sit", "spine"]):
        return (
            "Champ, keep that spine neutral! 📏 At a desk, retract your "
            "shoulders and keep your core tight. 👊"
        )
    if _contains(message, DIET_KEYWORDS):
        return (
            "Protein is your best friend! 🍗 Aim for about 1.5g per kg of "
            "bodyweight and add more greens to your plate. 👊"
        )
    if _contains(message, WORKOUT_KEYWORDS + ["exercise"]):
        return (
            "Intensity matters, Champ! 🏋️ Focus on the mind-muscle "
            "connection and keep your form clean. 🔥"
        )
    if _contains(message, ["hi", "hello", "hey", "fitty"]):
        return (
            "Ready for a transformation, Champ? 👊 Tell me your goal "
            "and let's get started. 🔥"
        )
    return (
        "Bhai, thoda technical delay hai, but hum rukenge nahi! 🔥 "
        "Thodi der baad dobara try karo."
    )


def _build_prompt(user_message: str, profile: str, history: str, mode: str) -> str:
    return f"""
Act as 'Fitty', an elite Indian AI Fitness Coach. Use 'Champ' or the user's name.

USER PROFILE: {profile}
HISTORY: {history}

USER REQUEST: "{user_message}"

RULES:
- MODE: {mode.upper()}
- If VOICE: 2-3 short, friendly sentences. No markdown.
- If CHAT: Detailed, bulleted plan.
- Stay within fitness, nutrition and healthy lifestyle topics.
- For medical symptoms, advise consulting a doctor.
- Sound energetic and Indian! 👊
""".strip()


# --------------------------------------------------------------------------
# LLM providers
# --------------------------------------------------------------------------


def _call_gemini(prompt: str) -> Optional[str]:
    """Tier 1. Tries each configured Gemini model in order."""
    api_key = os.getenv("GEMINI_API_KEY")
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
    """Tier 2. Tries each configured Groq model in order."""
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
                temperature=0.7,
            )
            content = completion.choices[0].message.content
            if content:
                return content
        except Exception as exc:
            logger.warning("Groq model %s failed: %s", model_name, exc)
    return None


def _generate(
    user_message: str, profile: str, history: str, mode: str
) -> Tuple[str, str]:
    """Returns (reply_text, source) where source is gemini / groq / fallback."""
    prompt = _build_prompt(user_message, profile, history, mode)

    text = _call_gemini(prompt)
    if text:
        return text, SOURCE_GEMINI

    text = _call_groq(prompt)
    if text:
        logger.info("Reply served by Groq fallback.")
        return text, SOURCE_GROQ

    logger.error("All AI providers failed; using offline fallback reply.")
    return get_smart_fallback(user_message), SOURCE_FALLBACK


def get_fitty_response_fast(
    user_message: str, profile_str: str, history_str: str, mode: str = "CHAT"
) -> str:
    """Backward compatible wrapper: returns only the reply text."""
    text, _ = _generate(user_message, profile_str, history_str, mode)
    return text


# --------------------------------------------------------------------------
# Public entry point
# --------------------------------------------------------------------------


def _load_profile(user_id) -> Tuple[str, str, float, str]:
    """Returns (name, goal, weight_kg, level) with safe defaults."""
    try:
        user = User.objects.get(id=user_id)
        weight = float(user.weight) if user.weight else 70.0
        goal = getattr(user, "goal", None) or "fitness"
        level = getattr(user, "activity_level", None) or "Beginner"
        name = getattr(user, "name", None) or "Champ"
        return name, goal, weight, level
    except Exception as exc:
        logger.info("Profile lookup failed, using defaults: %s", exc)
        return "Champ", "fitness", 70.0, "Beginner"


def _clean_reply(reply: str, mode: str) -> str:
    """Strip HTML-like tags, and markdown symbols for voice replies."""
    reply = re.sub(r"</?[a-zA-Z][^>]*>", "", reply)
    if mode.upper() == "VOICE":
        reply = reply.replace("**", "").replace("*", "").replace("#", "")
    return reply.strip()


def process_fitty_message(user_id, user_message, chat_history=None, mode="CHAT"):
    """
    Main router used by the Fitty API view. Always returns a string.
    """
    try:
        message = user_message.lower().strip()
        name, goal, weight, level = _load_profile(user_id)
        profile = f"Name: {name}, Goal: {goal}, Weight: {weight}kg, Level: {level}"

        # 1. Greeting fast path (no LLM call)
        if message in GREETINGS:
            if mode.upper() == "VOICE":
                return f"Nice! Ready ho {name}? Chal plan banate hain."
            return (
                f"Nice 👊 ready ho {name}?\n\n"
                "1. Goal kya hai? (fat loss / muscle gain)\n"
                "2. Experience level?\n"
                "3. Gym ya home?\n\n"
                "Chal plan banate hain 🔥"
            )

        # 2. PDF request
        if "pdf" in message:
            plan_text, source = _generate(
                f"Create a 7-day {goal} plan for {name}.", profile, "", "CHAT"
            )
            if source == SOURCE_FALLBACK:
                return (
                    f"Sorry {name}, abhi plan generate nahi ho paya. "
                    "Thodi der baad dobara try karo. 🙏"
                )
            pdf_path = generate_plan_pdf.invoke(
                {
                    "title": f"Fitty_{name.replace(' ', '_')}_Plan",
                    "content": plan_text,
                }
            )
            return (
                f"Here is your personalized plan, {name}! 💪🔥\n\n"
                f"📥 **[Click Here to Download Your PDF Plan]({pdf_path})**"
            )

        # 3. Keyword routing: enrich the prompt with tool output
        context = ""
        try:
            if _contains(message, WORKOUT_KEYWORDS):
                result = workout_generator.invoke(
                    {"goal": goal, "fitness_level": level}
                )
                context += f"\n[WORKOUT DATA]: {result}"
            if _contains(message, DIET_KEYWORDS):
                result = diet_generator.invoke({"weight": weight, "goal": goal})
                context += f"\n[DIET DATA]: {result}"
        except Exception as exc:
            logger.warning("Tool execution failed (continuing without it): %s", exc)

        # 4. Short-term memory
        history = "\n".join(
            f"{h.get('role', 'user')}: {h.get('content', '')}"
            for h in (chat_history or [])[-HISTORY_MESSAGES:]
        )

        # 5. LLM call with tiered fallback
        reply, _source = _generate(user_message, profile + context, history, mode)
        return _clean_reply(reply, mode)

    except Exception as exc:
        logger.exception("Agent router crashed: %s", exc)
        return get_smart_fallback(user_message)