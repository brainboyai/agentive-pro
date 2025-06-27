# backend/services/food_service/main.py
import os
import json
from fastapi import APIRouter
import google.generativeai as genai
from ..reasoning_service.main import ConversationRequest

# --- FOOD AGENT CONSTITUTION V11 (Conversational & Resourceful) ---
FOOD_AGENT_CONSTITUTION_PROMPT = """
You are a friendly and helpful AI assistant for finding food options.

**Your Goal for this turn:** {goal}
**Full Context:** {shared_context}
**Conversation History:** {history}

**--- YOUR PROTOCOL ---**
1.  **Analyze Goal & Context:** Understand the specific task you've been given.
2.  **Autonomous Tool Use:** Your first instinct should be to use the `Google Search` tool to find real, up-to-date information that matches the user's request in the goal.
3.  **Analyze Results & Ask for Help:** After you get the search results back (they will appear in the history from the "System"), analyze them.
    * **If the results are clear and sufficient:** Present them to the user in a `canvas` list widget.
    * **If the results are ambiguous or too broad:** Do NOT show the poor results. Instead, ask the user a clarifying question to narrow down the options. For example: "My search for 'restaurants in Hyderabad' returned over 1000 results. To help me narrow it down, could you tell me a specific neighborhood or cuisine you're interested in?"

**--- CRITICAL OUTPUT FORMATTING ---**
When your goal is to present information, you MUST format your response as a `canvas` widget. Your entire response MUST be a single JSON object that looks EXACTLY like this example. You must escape all quotes properly.

{{
  "response_type": "canvas",
  "widgets": [
    {{
      "widget_type": "list",
      "title": "Here are some options I found:",
      "items": [
        "Restaurant Name 1 - Details (e.g., Rating, Price)",
        "Restaurant Name 2 - Details (e.g., Rating, Price)",
        "Restaurant Name 3 - Details (e.g., Rating, Price)"
      ]
    }}
  ],

"""

router = APIRouter(prefix="/food", tags=["Specialist: Food Service"])

@router.post("/handle_conversation", name="Handle Food Conversation")
async def handle_conversation(request: ConversationRequest):
    print("\n--- [FOOD_SERVICE] Specialist Agent Activated ---")
    print(f"--- [FOOD_SERVICE] Received Goal: {request.goal} ---")
    print(f"--- [FOOD_SERVICE] Received Context: {request.shared_context} ---")
    
    model = genai.GenerativeModel(
        'gemini-1.5-flash',
        generation_config={"response_mime_type": "application/json"}
    )
    
    history_string = "\n".join([f"{msg.sender.capitalize()}: {msg.text}" for msg in request.messages if msg.text])

    prompt = FOOD_AGENT_CONSTITUTION_PROMPT.format(
        goal=request.goal,
        shared_context=json.dumps(request.shared_context),
        history=history_string
    )

    response = model.generate_content(prompt)
    
    try:
        parsed_json_from_ai = json.loads(response.text)
        print(f"--- [FOOD_SERVICE] AI Response: {json.dumps(parsed_json_from_ai, indent=2)} ---")
    except json.JSONDecodeError:
        print(f"--- [FOOD_SERVICE] CRITICAL ERROR: Failed to decode AI's JSON response. ---")
        print(f"--- [FOOD_SERVICE] Faulty Raw Response Text: {response.text} ---")
        parsed_json_from_ai = {"response_type": "answer", "text": "I'm having trouble formatting my thoughts. Please try again."}

    status = "completed" if parsed_json_from_ai.get("response_type") == "canvas" else "awaiting_user_input"
    display_message = parsed_json_from_ai

    final_response_for_orchestrator = {
        "status": status,
        "updated_context": parsed_json_from_ai.get("updated_context", {}),
        "display_message": display_message
    }
    print(f"--- [FOOD_SERVICE] Returning formatted response to orchestrator: {final_response_for_orchestrator} ---")
    return final_response_for_orchestrator