import os
import logging
import re
from accounts.models import User
from .tools import (
    workout_generator, 
    diet_generator, 
    generate_plan_pdf
)

logger = logging.getLogger(__name__)

def get_fitty_response_fast(user_message, profile_str, history_str, mode="CHAT"):
    """
    Direct call to Gemini SDK (Fast and Low Memory)
    """
    try:
        from google import genai
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            return "❌ API Key Missing."

        client = genai.Client(api_key=api_key)
        
        prompt = f"""
        Act as 'Fitty', an elite Indian AI Fitness Coach. Use 'Champ' or names.
        
        USER PROFILE:
        {profile_str}
        
        RECENT HISTORY:
        {history_str}
        
        USER REQUEST: "{user_message}"
        
        CRITICAL FORMATTING:
        - If MODE is VOICE: Keep response to EXACTLY 2-3 short, conversational sentences. No markdown (*).
        - If MODE is CHAT: Provide a detailed, bulleted, and professional plan.
        - NEVER say "I'll generate". Give the final answer NOW.
        """

        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt,
        )
        return response.text
    except Exception as e:
        logger.error(f"GenAI SDK Error: {e}")
        return "Bhai thoda brain freeze ho gaya... 2 sec me wapis try kar 🔥"

def process_fitty_message(user_id, user_message, chat_history=None, mode="CHAT"):
    """
    Ultra-Fast Hybrid Router using direct SDK.
    """
    try:
        msg = user_message.lower().strip()
        
        # FETCH PROFILE FAST
        try:
            user = User.objects.get(id=user_id)
            weight = float(user.weight) if user.weight else 70.0
            goal = getattr(user, 'goal', 'fitness')
            level = getattr(user, 'activity_level', 'Beginner')
            name = getattr(user, 'name', 'Champ')
        except Exception:
            weight, goal, level, name = 70.0, "fitness", "Beginner", "Champ"

        profile = f"Name: {name}, Goal: {goal}, Weight: {weight}kg, Level: {level}"

        # 1. FAST PATH: ZERO LATENCY GREETINGS
        if msg in ["hi", "hello", "hey", "namaste", "what's up", "hello fitty", "hi fitty"]:
            response_text = f"Nice 👊 ready ho {name}?\n\n1. Goal kya hai? (fat loss / muscle gain)\n2. Experience level?\n3. Gym ya home?\n\nChal plan banate hain 🔥Space"
            if mode.upper() == "VOICE":
                return f"Nice! Ready ho {name}? Chal plan banate hain."
            return response_text

        # 2. PDF GENERATION HOT-PATH
        if "pdf" in msg:
            # We still use the fast SDK for the content
            plan_content = get_fitty_response_fast(f"Create a 7-day {goal} plan for {name}.", profile, "", "CHAT")
            pdf_path = generate_plan_pdf.invoke({"title": f"Fitty_{name.replace(' ', '_')}_Plan", "content": plan_content})
            return f"Here is your highly structured personalized plan, {name}! 💪🔥\n\n📥 **[Click Here to Download Your Complete PDF Plan]({pdf_path})**"

        # 3. HYBRID ROUTER
        is_diet = any(w in msg for w in ["diet", "food", "eat", "meal", "nutrition", "calories", "protein"])
        is_workout = any(w in msg for w in ["workout", "exercise", "plan", "gym", "train", "chest", "legs", "gain", "loss"])
        
        contextual_data = ""
        if is_workout:
            contextual_data += f"\n[WORKOUT TIP]: {workout_generator.invoke({'goal': goal, 'fitness_level': level})}"
        if is_diet:
            contextual_data += f"\n[DIET TIP]: {diet_generator.invoke({'weight': weight, 'goal': goal})}"

        history_str = "\n".join([f"{h.get('role', 'user')}: {h.get('content', '')}" for h in (chat_history or [])[-4:]])
        
        # 4. GET RESPONSE VIA FAST SDK
        reply = get_fitty_response_fast(user_message, profile + contextual_data, history_str, mode)
        
        # Sanitize
        reply = re.sub(r'<.*?>', '', reply)
        if mode.upper() == "VOICE":
            reply = reply.replace("**", "").replace("*", "").replace("#", "")

        return reply

    except Exception as e:
        logger.error(f"Agent router crash: {e}")
        return "Bhai thoda issue aa gaya… 2 sec me try kar 🔥"