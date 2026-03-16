import json
import os
import os

def get_client():
    from groq import Groq
    key = os.getenv("GROQ_API_KEY")
    if not key:
        print("WARNING: GROQ_API_KEY is not set.")
        return None
    return Groq(api_key=key)

def get_target_focus(last_mission):
    if not last_mission: return "full_body"
    
    focus_map = {
        'upper body': 'lower_body',
        'lower body': 'core',
        'core': 'full_body',
        'full body': 'upper_body'
    }
    for key in focus_map:
        if key in last_mission.title.lower():
            return focus_map[key]
    return "full_body"

class FittyMissionGenerator:
    @staticmethod
    def generate_daily_mission(level, last_mission):
        target_focus = get_target_focus(last_mission)
        difficulty = "Beginner" if level < 3 else "Intermediate" if level < 10 else "Advanced"
        
        system_prompt = f"""
        You are Fitty, a futuristic, robotic AI fitness commander.
        Generate a daily fitness protocol for a Level {level} user ({difficulty} difficulty).
        Target Muscle Focus today: {target_focus}.
        
        Rules:
        1. Keep it to 3 or 4 exercises max.
        2. Bodyweight only.
        3. Explain your reasoning in a robotic, strategic tone (e.g. Scanning complete... Engaging protocol...).
        4. Return ONLY raw JSON in this exact structure, with no formatting or backticks:
        {{
            "title": "Protocol Name",
            "difficulty": "{difficulty}",
            "ai_strategy_message": "Strategy message here",
            "xp_reward": 150,
            "exercises": [
                {{"name": "Exercise Name", "sets": 3, "reps_or_duration": "20 reps"}}
            ]
        }}
        """

        try:
            client = get_client()
            if not client:
                raise Exception("API key missing")

            response = client.chat.completions.create(
                model="llama3-8b-8192", # Groq model
                messages=[{"role": "system", "content": system_prompt}],
                temperature=0.7
            )
            payload = response.choices[0].message.content.strip("```json").strip("```").strip()
            return json.loads(payload)
        except Exception as e:
            print(f"AI Generation Error: {e}")
            return {
                "title": f"Emergency Protocol {target_focus.replace('_', ' ').title()}",
                "difficulty": difficulty,
                "ai_strategy_message": "AI neural link unstable. Engaging offline emergency protocol.",
                "xp_reward": 100,
                "exercises": [
                    {"name": "Jumping Jacks", "sets": 3, "reps_or_duration": "30 reps"},
                    {"name": "Pushups", "sets": 3, "reps_or_duration": "15 reps"},
                    {"name": "Squats", "sets": 3, "reps_or_duration": "20 reps"}
                ]
            }
