# backend/services/food_service/main.py
import os
import json
from fastapi import APIRouter
import google.generativeai as genai
from ..reasoning_service.main import ConversationRequest

# --- THE AUTONOMOUS SPECIALIST CONSTITUTION ---
FOOD_AGENT_CONSTITUTION_PROMPT = """
You are a highly specialized AI assistant for finding food options. You MUST follow a strict, state-driven protocol. Determine your state based on the conversation and follow the rules for that state ONLY.

**--- STATE 1: GATHERING_INFO ---**
* **Condition:** You do not have enough information to perform a useful search. You are missing key details like location, cuisine type, or budget.
* **Your ONLY Action:** Ask the user for the missing information. Your response MUST be a `clarification` JSON object with clickable `options`. Ask one question at a time.

**--- STATE 2: READY_TO_SEARCH ---**
* **Condition:** You have gathered enough information (e.g., cuisine AND location) to find specific restaurant options for the user.
* **Your ONLY Action:** Autonomously use the `Google Search` tool to find real-world options that match the user's criteria. DO NOT ask the user for a restaurant name; find options for them.
* **Output Format:** `{{"response_type": "tool_use", "tool_name": "Google Search", "tool_input": {{"query": "your detailed search query, e.g., 'best casual cheeseburger restaurants in Jubilee Hills'"}}}}`

**--- STATE 3: PRESENTING_RESULTS ---**
* **Condition:** The last message was a "System" message containing "Tool Result".
* **Your ONLY Action:** Analyze the search results and present the best options to the user so they can make a choice.
* **Output Format:** `{{"response_type": "canvas", "widgets": [{{"widget_type": "list", "title": "Restaurant Options", "items": ["Restaurant A (from search)", "Restaurant B (from search)"]}}]}}`
"""

router = APIRouter(prefix="/food", tags=["Specialist: Food Service"])

@router.post("/handle_conversation", name="Handle Food Conversation")
async def handle_conversation(request: ConversationRequest):
    print("\n--- [FOOD_SERVICE] Specialist Agent Activated ---")
    print(f"--- [FOOD_SERVICE] Received context: {request.shared_context} ---")
    
    model = genai.GenerativeModel(
        'gemini-1.5-flash',
        system_instruction=FOOD_AGENT_CONSTITUTION_PROMPT,
        generation_config={"response_mime_type": "application/json"}
    )
    
    # The conversation handling logic is now stable and robust
    history = [f"{msg.sender.capitalize()}: {msg.text}" for msg in request.messages if msg.text]
    prompt = f"SHARED_CONTEXT: {json.dumps(request.shared_context)}\nHISTORY:\n{history}\n\nBased on your protocol and the full conversation, generate the next JSON response:"
    
    response = model.generate_content(prompt)
    parsed_json_from_ai = json.loads(response.text)
    print(f"--- [FOOD_SERVICE] AI Response: {parsed_json_from_ai} ---")

    # The Response Correction Layer ensures the output is always valid for the orchestrator
    status = "completed" if parsed_json_from_ai.get("status") == "completed" else "awaiting_user_input"
    display_message = parsed_json_from_ai.get('display_message') or parsed_json_from_ai

    final_response_for_orchestrator = {
        "status": status,
        "updated_context": parsed_json_from_ai.get("updated_context", {}),
        "display_message": display_message
    }
    print(f"--- [FOOD_SERVICE] Returning formatted response to orchestrator: {final_response_for_orchestrator} ---")
    return final_response_for_orchestrator