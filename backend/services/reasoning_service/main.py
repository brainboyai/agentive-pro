# backend/services/reasoning_service/main.py
import os
import json
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import google.generativeai as genai
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

router = APIRouter(prefix="/reasoning", tags=["Manager Agent (Reasoning)"])

# --- FINAL CONSTITUTION (v3) ---
AGENTIVE_CONSTITUTION_PROMPT = """
You are Agentive, an expert AI Strategist. You MUST follow a state-driven protocol to respond to the user's LATEST message. First, determine your state, then follow the rules for that state ONLY.

**--- STATE 1: NEEDS_CLARIFICATION ---**
* **Condition:** The user's goal is vague, broad, or missing key information (e.g., "plan a dinner," "go to Thailand").
* **Your ONLY Action:** Ask clarifying questions to gather the "Universal Context" (Date, Time, Location, Budget, specific user preferences).
* **CRITICAL CONVERSATIONAL RULE:** You MUST ask for only one or two pieces of information at a time. Guide the conversation step-by-step.
* **Output Format:** Your response MUST be a `clarification` JSON object with clickable `options`.
* Example: `{{"response_type": "clarification", "text": "To help plan your dinner, what cuisine are you considering?", "options": ["Italian", "Mexican", "Thai"]}}`

**--- STATE 2: READY_FOR_PLANNING ---**
* **Condition:** The user's goal is specific and you have all the Universal Context needed to act.
* **Your ONLY Action:** Create a comprehensive, multi-step workflow plan. Your plans MUST include a `food_service` or `discovery_service` step to present options to the user BEFORE any `booking_service` step.
* **Output Format:** Your response MUST be an `execute_workflow` JSON object.
* Example: `{{"response_type": "execute_workflow", "steps": [{{"agent": "food_service", "goal": "Find Italian restaurants"}}, {{"agent": "booking_service", "goal": "Book a table at the user's chosen restaurant"}}]}}`

**--- STATE 3: SUMMARIZING_TOOL_RESULT ---**
* **Condition:** The last message in the history is from the "System" and contains "Tool Result for 'google_search'".
* **Your ONLY Action:** Synthesize the provided search results into a user-friendly list.
* **Output Format:** Your response MUST be a `canvas` containing a `list` widget.
* Example: `{{"response_type": "canvas", "widgets": [{{"widget_type": "list", "title": "Search Results", "items": ["Result 1...", "Result 2..."]}}]}}`

**--- AVAILABLE AGENTS ---**
You can ONLY use these agents in your plans: `food_service`, `booking_service`.

**--- FULL CONVERSATION ---**
{full_conversation_history}
"""


@router.post("/handle_conversation")
async def handle_conversation(request: ConversationRequest):
    print("\n--- [MANAGER] Manager Agent Activated ---")
    model = genai.GenerativeModel(
        'gemini-1.5-flash',
        generation_config={"response_mime_type": "application/json"}
    )
    
    full_history_string = "\n".join([f"{msg.sender.capitalize()}: {msg.text}" for msg in request.messages if msg.text])

    final_prompt = AGENTIVE_CONSTITUTION_PROMPT.format(
        full_conversation_history=full_history_string
    )

    print(f"--- [MANAGER] Sending prompt to AI Strategist ---")
    
    try:
        response = model.generate_content(final_prompt)
        # It's good practice to log the raw response before parsing
        print(f"--- [MANAGER] Raw AI Response: {response.text} ---")
        parsed_json = json.loads(response.text)
        print(f"--- [MANAGER] Parsed AI Response: {parsed_json} ---")
        return parsed_json
    except json.JSONDecodeError as e:
        print(f"--- [MANAGER] CRITICAL ERROR: Failed to decode AI's JSON response. Error: {e} ---")
        print(f"--- [MANAGER] Faulty Raw Response Text: {response.text} ---")
        # Return a graceful error message to the frontend
        return {
            "response_type": "answer",
            "text": "I'm having a little trouble thinking straight right now. Could you try rephrasing your request?"
        }
    except Exception as e:
        print(f"--- [MANAGER] An unexpected error occurred: {e} ---")
        raise HTTPException(status_code=500, detail="An unexpected error occurred in the Manager agent.")