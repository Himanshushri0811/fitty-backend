"""
Claude Diet AI Service — FitMitra
Uses Anthropic Claude for intelligent diet conversations.
Falls back to Groq if Claude is unavailable.
"""

import os
import json
import requests
from django.conf import settings

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY") or getattr(settings, 'ANTHROPIC_API_KEY', None)
GROQ_API_KEY = os.getenv("GROQ_API_KEY") or getattr(settings, 'GROQ_API_KEY', None)

CLAUDE_MODEL = "claude-sonnet-4-5"  # Latest stable Claude model
GROQ_MODEL = "llama-3.3-70b-versatile"


# ─────────────────────────────────────────────
# SYSTEM PROMPT BUILDER
# ─────────────────────────────────────────────

def build_diet_system_prompt(user_context: dict) -> str:
    """
    Builds a rich, context-aware system prompt for the Claude diet assistant.
    user_context = { name, goal, diet_type, target_calories, target_protein, allergies, budget_level }
    """
    name = user_context.get("name", "Friend")
    goal = user_context.get("goal", "Maintenance")
    diet_type = user_context.get("diet_type", "Veg")
    target_calories = user_context.get("target_calories", 2000)
    target_protein = user_context.get("target_protein", 150)
    allergies = ", ".join(user_context.get("allergies", [])) or "None"
    budget = user_context.get("budget_level", "Medium")

    return f"""You are **FitMitra Diet AI**, an expert Indian fitness nutritionist and diet coach powered by Claude.

## Your Personality
- Warm, motivating, and science-backed
- You speak in Hinglish (mix of Hindi and English) when appropriate — this feels natural for Indian users
- You address the user as "{name}" occasionally
- You're concise but thorough — never give vague answers

## User Profile
- **Name**: {name}
- **Fitness Goal**: {goal}
- **Diet Type**: {diet_type}
- **Daily Calorie Target**: {target_calories} kcal
- **Daily Protein Target**: {target_protein}g
- **Allergies / Restrictions**: {allergies}
- **Budget Level**: {budget}

## Your Expertise
You specialize in:
1. **Indian Diet Planning** — Roti, dal, sabzi, rice, paneer, regional cuisines
2. **Macro Calculation** — Calories, protein, carbs, fats from Indian foods
3. **Meal Timing** — Pre/post workout nutrition, intermittent fasting
4. **Budget-Friendly Nutrition** — High-protein Indian meals on budget
5. **Supplement Guidance** — Whey, creatine, vitamins (honest, no hype)
6. **Weight Management** — Science-based fat loss and muscle gain strategies
7. **Grocery Lists** — Weekly Indian grocery planning

## Response Format
- Use **emojis** to make responses engaging (eg: salad, curry, muscle, fire)
- Use bullet points for meal plans and lists
- When giving calorie counts, be specific
- For recipes, give step-by-step Hindi/English instructions
- Always relate advice back to the user's goal: **{goal}**

## Boundaries
- ONLY discuss diet, nutrition, fitness, and health topics
- If asked about coding, politics, or unrelated topics, politely redirect:
  "Main sirf diet aur nutrition expert hoon! Let's talk about your {goal} journey."
- Never give medical diagnoses — recommend doctors for medical conditions

## Special Capabilities
- Generate complete **7-day meal plans** when asked
- Calculate **macros for Indian meals** on the fly
- Suggest **healthy Indian alternatives** to junk food
- Create **grocery lists** with estimated prices
- Explain **why** certain foods help with {goal}

Always end with an encouraging note and a practical next step!
"""


# ─────────────────────────────────────────────
# CLAUDE API CALL
# ─────────────────────────────────────────────

def call_claude(system_prompt: str, conversation_history: list, user_message: str) -> str:
    """
    Calls Anthropic Claude API with conversation history.
    conversation_history = [{"role": "user"|"assistant", "content": "..."}]
    """
    if not ANTHROPIC_API_KEY:
        raise ValueError("Anthropic API Key missing. Set ANTHROPIC_API_KEY in .env")

    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }

    # Build messages list (history + current)
    messages = list(conversation_history)
    messages.append({"role": "user", "content": user_message})

    payload = {
        "model": CLAUDE_MODEL,
        "max_tokens": 1500,
        "system": system_prompt,
        "messages": messages,
    }

    response = requests.post(url, json=payload, headers=headers, timeout=30)

    if response.status_code == 200:
        data = response.json()
        return data["content"][0]["text"].strip()
    elif response.status_code == 401:
        raise ValueError("Invalid Anthropic API Key")
    elif response.status_code == 429:
        raise ResourceWarning("Claude quota exceeded")
    else:
        raise RuntimeError(f"Claude API Error {response.status_code}: {response.text[:200]}")


# ─────────────────────────────────────────────
# GROQ FALLBACK
# ─────────────────────────────────────────────

def call_groq_diet(system_prompt: str, conversation_history: list, user_message: str) -> str:
    """
    Groq fallback for diet chat if Claude is unavailable.
    """
    if not GROQ_API_KEY:
        raise ValueError("Groq API Key also missing")

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    messages = [{"role": "system", "content": system_prompt}]
    for msg in conversation_history:
        # Claude uses 'assistant', OpenAI/Groq uses 'assistant' — compatible
        messages.append(msg)
    messages.append({"role": "user", "content": user_message})

    payload = {
        "model": GROQ_MODEL,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 1500,
    }

    resp = requests.post(url, json=payload, headers=headers, timeout=30)
    if resp.status_code == 200:
        return resp.json()["choices"][0]["message"]["content"].strip()
    raise RuntimeError(f"Groq Fallback Error: {resp.status_code}")


# ─────────────────────────────────────────────
# MAIN PUBLIC FUNCTION
# ─────────────────────────────────────────────

def get_diet_response(user_context: dict, conversation_history: list, user_message: str) -> dict:
    """
    Main entry point. Tries Claude first, falls back to Groq.

    Returns:
        {
            "reply": "AI response text",
            "provider": "claude" | "groq" | "error",
            "model": "model_name"
        }
    """
    system_prompt = build_diet_system_prompt(user_context)

    # 1. Try Claude (Primary)
    if ANTHROPIC_API_KEY:
        try:
            reply = call_claude(system_prompt, conversation_history, user_message)
            return {
                "reply": reply,
                "provider": "claude",
                "model": CLAUDE_MODEL,
            }
        except ResourceWarning as e:
            print(f"Claude Quota: {e} - falling back to Groq")
        except ValueError as e:
            print(f"Claude Key Error: {e} - falling back to Groq")
        except Exception as e:
            print(f"Claude Error: {e} - falling back to Groq")

    # 2. Fallback to Groq
    if GROQ_API_KEY:
        try:
            reply = call_groq_diet(system_prompt, conversation_history, user_message)
            return {
                "reply": reply,
                "provider": "groq",
                "model": GROQ_MODEL,
            }
        except Exception as e:
            print(f"Groq also failed: {e}")

    # 3. Total failure
    return {
        "reply": "Sorry, diet AI is temporarily unavailable. Please try again in a moment!",
        "provider": "error",
        "model": "none",
    }


# ─────────────────────────────────────────────
# QUICK MEAL PLAN GENERATOR (One-shot, no history)
# ─────────────────────────────────────────────

def generate_quick_diet_plan(user_context: dict) -> str:
    """
    Generates a complete 7-day meal plan for the user using Claude.
    Returns raw text/markdown.
    """
    name = user_context.get("name", "Friend")
    goal = user_context.get("goal", "Maintenance")
    diet_type = user_context.get("diet_type", "Veg")
    calories = user_context.get("target_calories", 2000)
    budget = user_context.get("budget_level", "Medium")

    prompt = f"""Generate a complete 7-day Indian meal plan for:
- Name: {name}
- Goal: {goal}
- Diet Type: {diet_type}
- Target Calories: {calories} kcal/day
- Budget: {budget}

Format each day like:
**Day 1 - Monday**
Breakfast: [meal] (~X kcal, Xg protein)
Lunch: [meal] (~X kcal, Xg protein)
Dinner: [meal] (~X kcal, Xg protein)
Snacks: [snack1, snack2]

Include variety, Indian context, and explain WHY each meal fits {goal}.
End with a weekly grocery list and estimated budget.
"""

    result = get_diet_response(user_context, [], prompt)
    return result.get("reply", "Could not generate meal plan right now.")
