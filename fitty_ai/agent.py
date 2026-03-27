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

def get_smart_fallback(message):
    """
    Context-aware fallback when AI SDK fails (Quota/Timeout)
    """
    msg = message.lower()
    
    if any(w in msg for w in ["water", "hydrate", "drink"]):
        return "Bhai, hydration is key! 💧 Aim for 3-4 liters daily. Quick tip: Carry a bottle everywhere to stay on track. Gemini is resting, but Fitty is always here! 🔥"
    
    if any(w in msg for w in ["posture", "back", "sit", "spine"]):
        return "Champ, keep that spine neutral! 📏 If you're at a desk, retract your shoulders and keep your core tight. Posture check complete! Gemini will be back soon. 👊"
    
    if any(w in msg for w in ["workout", "exercise", "train", "gym", "chest", "legs"]):
        return "Intensity matters, Champ! 🏋️ Focus on the mind-muscle connection. Even if the AI is a bit slow right now, don't let your workout slow down! Keep pushing! 🔥"
    
    if any(w in msg for w in ["diet", "food", "eat", "meal", "nutrition", "protein"]):
        return "Protein is your best friend! 🍗 Aim for 1.5g per kg of bodyweight. Add more greens to your plate. I'm having a small tech glitch, but your nutrition shouldn't! 👊"

    if any(w in msg for w in ["hi", "hello", "hey", "fitty"]):
        return "Ready for a transformation, Champ? 👊 Tell me your goal and let's get started. Gemini is slightly busy, but I'm ready for you! 🔥"

    return "Bhai, thoda technical delay hai background me, but hum rukenge nahi! 🔥 Aaj ka target pura karna hai. Try asking for a workout or diet tip! 👊"

def get_fitty_response_fast(user_message, profile_str, history_str, mode="CHAT"):
    """
    Tiered Reliability: Gemini -> Groq -> Smart Fallback
    """
    prompt = f"""
    Act as 'Fitty', an elite Indian AI Fitness Coach. Use 'Champ' or names.
    
    USER PROFILE: {profile_str}
    HISTORY: {history_str}
    
    USER REQUEST: "{user_message}"
    
    RULES:
    - MODE: {mode.upper()}
    - If VOICE: 2-3 short, friendly sentences. No markdown (*).
    - If CHAT: Detailed, bulleted plan.
    - Sound energetic and Indian! 👊
    """

    # TIER 1: GEMINI (High context quality)
    try:
        from google import genai
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model='gemini-1.5-flash',
                contents=prompt,
            )
            if response and response.text:
                return response.text
    except Exception as gemini_err:
         print(f"🔴 Tier 1 (Gemini) Failed: {gemini_err}")
         logger.warning(f"Tier 1 (Gemini) failed: {gemini_err}")

    # TIER 2: GROQ (Ultra-fast stable fallback)
    try:
        from groq import Groq
        groq_key = os.getenv("GROQ_API_KEY")
        if groq_key:
            client = Groq(api_key=groq_key)
            # Try a mix of models for better hit rate
            models = ["llama-3.3-70b-versatile", "llama-3.1-70b-versatile", "llama3-70b-8192"]
            last_err = None
            for model_name in models:
                try:
                    completion = client.chat.completions.create(
                        messages=[{"role": "user", "content": prompt}],
                        model=model_name,
                        temperature=0.7,
                    )
                    if completion.choices[0].message.content:
                        return completion.choices[0].message.content
                except Exception as model_err:
                    last_err = model_err
                    continue
            if last_err: print(f"🔴 Tier 2 (Groq) Failed: {last_err}")
    except Exception as groq_err:
        print(f"🔴 Tier 2 (Groq) Fatal: {groq_err}")
        logger.warning(f"Tier 2 (Groq) failed: {groq_err}")

    # TIER 3: SMART OFFLINE FALLBACK
    return get_smart_fallback(user_message)

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
            response_text = f"Nice 👊 ready ho {name}?\n\n1. Goal kya hai? (fat loss / muscle gain)\n2. Experience level?\n3. Gym ya home?\n\nChal plan banate hain 🔥"
            if mode.upper() == "VOICE":
                return f"Nice! Ready ho {name}? Chal plan banate hain."
            return response_text

        # 2. PDF GENERATION HOT-PATH
        if "pdf" in msg:
            plan_content = get_fitty_response_fast(f"Create a 7-day {goal} plan for {name}.", profile, "", "CHAT")
            pdf_path = generate_plan_pdf.invoke({"title": f"Fitty_{name.replace(' ', '_')}_Plan", "content": plan_content})
            return f"Here is your highly structured personalized plan, {name}! 💪🔥\n\n📥 **[Click Here to Download Your Complete PDF Plan]({pdf_path})**"

        # 3. HYBRID ROUTER (Safely enrich prompt if possible)
        is_diet = any(w in msg for w in ["diet", "food", "eat", "meal", "nutrition", "calories", "protein"])
        is_workout = any(w in msg for w in ["workout", "exercise", "plan", "gym", "train", "chest", "legs", "gain", "loss"])
        
        contextual_data = ""
        try:
            if is_workout:
                contextual_data += f"\n[WORKOUT TIP]: {workout_generator.invoke({'goal': goal, 'fitness_level': level})}"
            if is_diet:
                contextual_data += f"\n[DIET TIP]: {diet_generator.invoke({'weight': weight, 'goal': goal})}"
        except Exception as tool_err:
             logger.warning(f"Optional tools failed (ignoring): {tool_err}")

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
        return get_smart_fallback(user_message)

