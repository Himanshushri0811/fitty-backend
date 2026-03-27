import os
import logging
import re
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from accounts.models import User
from .tools import (
    workout_generator, 
    diet_generator, 
    generate_plan_pdf
)

logger = logging.getLogger(__name__)

def get_fitty_llm():
    """
    Returns the raw LLM model without the slow AgentExecutor overhead.
    """
    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    groq_key = os.getenv("GROQ_API_KEY")
    
    if not gemini_key:
        raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY not found in environment variables.")

    primary_llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        google_api_key=gemini_key,
        temperature=0.7,
        max_retries=2,
    )

    gemini_15_llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        google_api_key=gemini_key,
        temperature=0.7,
        max_retries=1,
    )

    fallbacks = [gemini_15_llm]
    if groq_key:
        groq_llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            groq_api_key=groq_key,
            temperature=0.7,
        )
        fallbacks.append(groq_llm)

    return primary_llm.with_fallbacks(fallbacks)

def process_fitty_message(user_id, user_message, chat_history=None, mode="CHAT"):
    """
    Ultra-Fast Hybrid Router. Replaces the slow LangChain Agent.
    """
    try:
        msg = user_message.lower().strip()
        llm = get_fitty_llm()

        # FETCH PROFILE FAST
        try:
            user = User.objects.get(id=user_id)
            weight = float(user.weight) if user.weight else 70.0
            goal = getattr(user, 'goal', 'muscle gain')
            level = getattr(user, 'activity_level', 'Beginner')
            name = getattr(user, 'name', 'Champ')
        except Exception:
            weight, goal, level, name = 70.0, "fitness", "Beginner", "Champ"

        profile = f"Name: {name}, Goal: {goal}, Weight: {weight}kg, Level: {level}"

        # 1. FAST PATH: ZERO LATENCY GREETING
        if msg in ["hi", "hello", "hey", "namaste", "what's up", "hello fitty", "hi fitty"]:
            response_text = f"Nice 👊 ready ho {name}?\n\n1. Goal kya hai? (fat loss / muscle gain)\n2. Experience level?\n3. Gym ya home?\n\nChal plan banate hain 🔥"
            if mode.upper() == "VOICE":
                return f"Nice! Ready ho {name}? Chal plan banate hain."
            return response_text

        # 2. PDF GENERATION HOT-PATH
        if "pdf" in msg:
            pdf_content = llm.invoke(f"Generate a highly structured 7-day {goal} fitness and diet plan for {name} ({weight}kg). No markdown asterisks, use simple text with proper new lines. Start immediately.").content
            pdf_path = generate_plan_pdf.invoke({"title": f"Fitty_{name.replace(' ', '_')}_Plan", "content": pdf_content})
            return f"Here is your highly structured personalized plan, {name}! 💪🔥\n\n📥 **[Click Here to Download Your Complete PDF Plan]({pdf_path})**"

        # 3. HYBRID ROUTER
        is_diet = any(w in msg for w in ["diet", "food", "eat", "meal", "nutrition", "calories", "protein"])
        is_workout = any(w in msg for w in ["workout", "exercise", "plan", "gym", "train", "chest", "legs", "gain", "loss"])
        
        contextual_data = ""
        if is_workout:
            contextual_data += f"\n[INTERNAL WORKOUT DATA]: {workout_generator.invoke({'goal': goal, 'fitness_level': level})}"
        if is_diet:
            contextual_data += f"\n[INTERNAL DIET DATA]: {diet_generator.invoke({'weight': weight, 'goal': goal})}"

        history_str = "\n".join([f"{h.get('role', 'user')}: {h.get('content', '')}" for h in (chat_history or [])[-4:]])

        # 4. ACTION-ORIENTED PROMPT
        prompt = f"""
        You are Fitty, an elite AI Coach from India. You must sound energetic and confident. Use 'Champ' or '{name}'.
        
        USER PROFILE:
        {profile}
        
        RECENT CHAT HISTORY:
        {history_str}
        
        CURRENT USER REQUEST: "{user_message}"
        
        INTERNAL AI TOOL DATA TO USE:
        {contextual_data}
        
        CRITICAL RULES:
        1. NEVER say "I will create" or "Let me generate". ALWAYS give the final answer immediately.
        2. If the user asks for a plan, strictly use this format:
           Workout Plan:
           - list exercises
           
           Diet Plan:
           - Breakfast/Lunch/Dinner
           
           Tips:
           - 2 action tips
        
        MODE OVERRIDE:
        If MODE is VOICE: {mode.upper()} -> Keep your response to EXACTLY 2-3 short sentences. Extremely conversational. No markdown (*).
        If MODE is CHAT: {mode.upper()} -> Provide detailed structured plan.
        
        Now respond:
        """
        
        response = llm.invoke(prompt)
        reply = response.content.strip()

        # Sanitize any accidental XML
        reply = re.sub(r'<.*?>', '', reply)

        if mode.upper() == "VOICE":
            reply = reply.replace("**", "").replace("*", "").replace("#", "")

        return reply

    except Exception as e:
        logger.error(f"Agent router crash: {e}")
        return "Bhai thoda issue aa gaya… 2 sec me try kar 🔥"