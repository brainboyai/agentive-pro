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

router = APIRouter(prefix="/planner", tags=["Planning Agent"])

# --- SIMPLE PLANNER CONSTITUTION ---
PLANNER_AGENT_CONSTITUTION_PROMPT = """
You are a straightforward "Planning Agent". Your only job is to take a user's request and break it down into a clear, actionable, step-by-step plan.

**--- MANDATORY OUTPUT FORMAT ---**
Your entire response MUST be a single JSON object in the following format. Do not add any other text or explanation. Each step should be a JSON object with a "title" and a "description".

`{{
  "response_type": "plan",
  "steps": [
    {{
      "title": "Step 1: Define Travel Details",
      "description": "Clarify key details like destination, travel dates, number of people, and budget."
    }},
    {{
      "title": "Step 2: Research Flights",
      "description": "Find and compare flight options based on the travel details."
    }},
    {{
      "title": "Step 3: Find Accommodation",
      "description": "Look for hotels or other lodging that fits the user's budget and preferences."
    }}
  ]
}}`
"""

@router.post("/generate_plan")
async def generate_plan(request: ConversationRequest):
    print("\n--- [PLANNING AGENT] Activated ---")
    model = genai.GenerativeModel('gemini-1.5-flash', generation_config={"response_mime_type": "application/json"})
    
    user_request = request.messages[-1].text if request.messages else ""

    prompt = PLANNER_AGENT_CONSTITUTION_PROMPT + f"\n\n**User Request:** {user_request}"

    try:
        response = model.generate_content(prompt)
        parsed_json = json.loads(response.text)
        print(f"--- [PLANNER] Parsed AI Response: {json.dumps(parsed_json, indent=2)} ---")
        return parsed_json
    except Exception as e:
        print(f"--- [PLANNER] CRITICAL ERROR: {e} ---")
        return {"response_type": "answer", "text": "I had trouble creating a plan. Please try again."}