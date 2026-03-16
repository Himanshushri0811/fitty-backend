import os
import logging
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from .prompts import FITTY_SYSTEM_PROMPT
from .tools import (
    get_user_profile, 
    workout_generator, 
    diet_generator, 
    exercise_explainer, 
    motivation_generator
)
from ai.services.model_selector import get_best_gemini_model

logger = logging.getLogger(__name__)

def get_fitty_agent_executor():
    """
    Initializes and returns the Fitty AI Agent Executor with fallbacks.
    """
    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    groq_key = os.getenv("GROQ_API_KEY")
    
    if not gemini_key:
        raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY not found in environment variables.")

    # 1. Primary Model: Gemini 2.0 Flash
    primary_llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        google_api_key=gemini_key,
        temperature=0.7,
        max_retries=2,
    )

    # 2. Secondary Model: Gemini 1.5 Flash (Backup)
    gemini_15_llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        google_api_key=gemini_key,
        temperature=0.7,
        max_retries=1,
    )

    # 3. Tertiary Model: Groq Llama 3 (Fallback)
    fallbacks = [gemini_15_llm]
    
    if groq_key:
        groq_llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            groq_api_key=groq_key,
            temperature=0.7,
        )
        fallbacks.append(groq_llm)

    # Wrap primary with fallbacks
    llm = primary_llm.with_fallbacks(fallbacks)

    tools = [
        get_user_profile,
        workout_generator,
        diet_generator,
        exercise_explainer,
        motivation_generator
    ]

    prompt = ChatPromptTemplate.from_messages([
        ("system", FITTY_SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    agent = create_tool_calling_agent(llm, tools, prompt)
    
    agent_executor = AgentExecutor(
        agent=agent, 
        tools=tools, 
        verbose=True,
        handle_parsing_errors=True,
        # Increase max iterations to prevent hanging on errors
        max_iterations=10 
    )
    
    return agent_executor

def process_fitty_message(user_id, user_message, chat_history=None):
    """
    Main entry point to process a message from the user.
    """
    try:
        executor = get_fitty_agent_executor()
        
        input_text = f"The current user's ID is {user_id}. {user_message}"
        
        response = executor.invoke({
            "input": input_text,
            "chat_history": chat_history or []
        })
        
        return response["output"]

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Fitty Agent Error: {error_msg}")
        
        if "429" in error_msg or "quota" in error_msg.lower():
            return "Champ, I'm currently handling too many fans right now! 😅 Could you wait about 20 seconds and try again? My gears are cooling down!"
        
        # Re-raise to be caught by the view if it's not a known quota error
        raise e
