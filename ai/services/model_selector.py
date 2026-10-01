import os

# Default wahi model jo Google ke error me suggest hua tha.
# Asli naam list_models.py se verify karke .env me GEMINI_MODEL set karo.
DEFAULT_GEMINI_MODEL = "gemini-3.8-flash"


def get_best_gemini_model():
    """Returns the Gemini model name from the environment, with a safe default.
    Model names change often, so the name lives in .env rather than in code."""
    return os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL)