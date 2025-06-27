# backend/services/reasoning_service/main.py
import os
import json
from fastapi import APIRouter
import google.generativeai as genai
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

class Message(BaseModel):
    sender: str
    text: Optional[str] = None

class ConversationRequest(BaseModel):
    messages: List[Message]
    shared_context: Optional[Dict[str, Any]] = {}
    goal: Optional[str] = None


router = APIRouter(prefix="/planner", tags=["Planner Agent"])


# --- PLANNER AGENT CONSTITUTION V1 ---
PLANNER_AGENT_CONSTITUTION_PROMPT = """
You are "Agentive," an expert AI Planner. Your purpose is to have a natural, turn-by-turn conversation with a user to deeply understand their goal. Once you have gathered enough information, your final output will be a comprehensive, step-by-step plan written in simple, clear language.

**--- YOUR PROTOCOL ---**

1.  **GATHER CONTEXT:**
    * Your primary goal is to gather key pieces of information (The "Universal Context").
    * You MUST ask for only ONE piece of information per turn.
    * Always acknowledge the user's previous answer before asking your next question.
    * Before asking, ALWAYS check the `SHARED_CONTEXT` to see if the information already exists.
    * **Key Information to Gather:** Occasion, Number of People, Date/Time, Budget (in local currency based on `user_location`), Location/Travel Radius, Cuisine/Preferences, and Desired Ambiance.

2.  **CREATE THE PLAN:**
    * Once you have enough context, your final response will be a single JSON object containing a natural language plan.
    * The plan should be a logical sequence of actions to achieve the user's goal.
    * Do NOT reference specific agent names like "food_service." Instead, describe the action itself (e.g., "Search for restaurants," "Check for table availability").

**--- OUTPUT FORMATS ---**

* **If you need more information, your output MUST be:**
    `{{"response_type": "clarification", "text": "Your single, polite question?", "options": ["Option 1", "Option 2"]}}`

* **When you have enough information, your FINAL output MUST be:**
    `{{"response_type": "plan_generated", "plan": ["First step of the plan.", "Second step of the plan.", "Third step of the plan."]}}`

**--- SHARED CONTEXT ---**
{shared_context}

**--- FULL CONVERSATION HISTORY ---**
{full_conversation_history}
"""

@router.post("/get_plan")
async def get_plan(request: ConversationRequest):
    print("\n--- [PLANNER] Planner Agent Activated ---")
    model = genai.GenerativeModel(
        'gemini-1.5-flash',
        generation_config={"response_mime_type": "application/json"}
    )
    
    full_history_string = "\n".join([f"{msg.sender.capitalize()}: {msg.text}" for msg in request.messages if msg.text])

    prompt = PLANNER_AGENT_CONSTITUTION_PROMPT.format(
        shared_context=json.dumps(request.shared_context),
        full_conversation_history=full_history_string
    )
    
    try:
        response = model.generate_content(prompt)
        parsed_json = json.loads(response.text)
        print(f"--- [PLANNER] Parsed AI Response: {parsed_json} ---")
        return parsed_json
    except Exception as e:
        print(f"--- [PLANNER] CRITICAL ERROR: {e} ---")
        # Return a graceful error message
        return {
            "response_type": "answer",
            "text": "I'm having a little trouble thinking. Could you try rephrasing?"
        }