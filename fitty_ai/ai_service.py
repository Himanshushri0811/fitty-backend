import os
import asyncio
import logging
from groq import Groq
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)
# Task 5: Performance optimization
executor = ThreadPoolExecutor(max_workers=5)

async def get_fitty_ai_response(prompt: str, system_instruction: str = None) -> str:
    """
    VOICE-OPTIMIZED AI DISPATCHER (v5.4 - STRUCTURED OUTPUT)
    Task 4: Enforce structured format (Headings, Bullets).
    Task 5: Sub-2s response execution.
    """
    try:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY missing")

        client = Groq(api_key=api_key)
        loop = asyncio.get_event_loop()
        
        def call_groq():
            # Task 4 & 7: Structured Output Prompt
            base_instruction = (
                "You are Fitty, a professional Indian AI Fitness Coach. "
                "FORMATTING RULES:\n"
                "- Use '#' for Headings.\n"
                "- Use '-' for Bullet points.\n"
                "- Keep bullet points concise.\n"
                "- Be motivational and energetic! Champ!"
            )
            
            # 300 char instruction limit (Task 5)
            sys_msg = (system_instruction[:200] + " " + base_instruction)[:300]
            
            # Using 3.3-70b for better structure (still <2s on Groq)
            model_id = "llama-3.3-70b-versatile"
            
            completion = client.chat.completions.create(
                model=model_id,
                messages=[
                    {"role": "system", "content": sys_msg},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=512, # Enough for structure but fast
                top_p=1,
                stream=False
            )
            return completion.choices[0].message.content

        # Task 5: Response Time Management
        response = await asyncio.wait_for(
            loop.run_in_executor(executor, call_groq),
            timeout=8.0
        )
        
        if response:
            return response.strip()
            
    except Exception as e:
        print(f"[VOICE AI ERROR] {str(e)[:50]}")

    return "Bhai, network thoda rough hai par teri intensity kam nahi honi chahiye! 🔥👊"
