import os
from django.conf import settings

def get_best_gemini_model():
    """
    Returns the preferred model directly to save API quota from unnecessary test calls.
    Using gemini-2.0-flash as it is the most modern and supported version.
    """
    return "gemini-2.0-flash"
