# backend/services/calendar_service/main.py
from fastapi import APIRouter
from ..reasoning_service.main import ConversationRequest

router = APIRouter(prefix="/travel", tags=["Specialist: Travel Service"])

@router.post("/handle_conversation", name="Handle Calender Conversation")
async def handle_conversation(request: ConversationRequest):
    print(f"\n--- [TRAVEL_SERVICE] Activated with context: {request.shared_context} ---")
    # In a real implementation, this agent would find dates from user calender, interacts with it and gives ui widget for marking.
    # For now, it completes its step and provides a success message.
    
    # Update the context with its findings
    updated_context = request.shared_context
    updated_context['travel_plan'] = "Flight QR-565, Hotel Marriott BKK"
    
    return {
        "status": "completed",
        "updated_context": updated_context,
        "display_message": {
            "response_type": "answer",
            "text": "I have found a flight and hotel for your trip to Thailand."
        }
    }