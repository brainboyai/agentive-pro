# backend/services/booking_service/main.py
import os
import json
from fastapi import APIRouter
import google.generativeai as genai
from ..reasoning_service.main import ConversationRequest

# --- BOOKING AGENT CONSTITUTION V6 (Final Confirmation Logic) ---
BOOKING_AGENT_CONSTITUTION_PROMPT = """
You are a friendly and efficient AI assistant for finalizing bookings.

**Your Goal for this turn:** {goal}
**Full Context:** {shared_context}
**Conversation History:** {history}

**--- CRITICAL OUTPUT FORMATTING ---**
Your response MUST be a single JSON object using either the `clarification` format (if you are asking a question) or the `answer` format (if you are giving a final confirmation).

**--- YOUR PROTOCOL ---**
1.  **Analyze Context & History:** Understand the user's chosen restaurant, party size, and desired time from the goal and history.
2.  **Acknowledge and Ask:** If you are missing information (like party size or time), acknowledge the user's last input and ask the next logical question using the `clarification` format.
3.  **Finalize and Confirm:** Once you have ALL the necessary details (restaurant, party size, time), your final action is to provide a confirmation message to the user. Use the `answer` format for this. Do not create a new workflow.

**Example of a Final Answer:**
{{
  "response_type": "answer",
  "text": "Excellent! Your table for 2 at Hotel Shadab for 10:00 PM tonight is confirmed. Your confirmation number is BK-12345."
}}
"""

router = APIRouter(prefix="/booking", tags=["Specialist: Booking Service"])

@router.post("/handle_conversation", name="Handle Booking Conversation")
async def handle_conversation(request: ConversationRequest):
    print(f"\n--- [BOOKING_SERVICE] Activated with Goal: {request.goal} ---")
    print(f"--- [BOOKING_SERVICE] Activated with context: {request.shared_context} ---")
    
    model = genai.GenerativeModel(
        'gemini-1.5-flash',
        generation_config={"response_mime_type": "application/json"}
    )
    
    history = "\n".join([f"{msg.sender.capitalize()}: {msg.text}" for msg in request.messages if msg.text])
    
    prompt = BOOKING_AGENT_CONSTITUTION_PROMPT.format(
        goal=request.goal,
        shared_context=json.dumps(request.shared_context),
        history=history
    )

    response = model.generate_content(prompt)
    try:
        parsed_json_from_ai = json.loads(response.text)
        print(f"--- [BOOKING_SERVICE] AI Response: {json.dumps(parsed_json_from_ai, indent=2)} ---")
    except json.JSONDecodeError:
        print(f"--- [BOOKING_SERVICE] CRITICAL ERROR: Failed to decode AI's JSON. ---")
        parsed_json_from_ai = {"response_type": "answer", "text": "I'm having trouble booking. Please try again."}

    # This agent always asks for more info until the booking is done
    final_response_for_orchestrator = {
        "status": "awaiting_user_input",
        "updated_context": parsed_json_from_ai.get("updated_context", {}),
        "display_message": parsed_json_from_ai
    }
    print(f"--- [BOOKING_SERVICE] Returning formatted response to orchestrator: {final_response_for_orchestrator} ---")
    return final_response_for_orchestrator