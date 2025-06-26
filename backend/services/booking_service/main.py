# backend/services/booking_service/main.py
from fastapi import APIRouter
from ..reasoning_service.main import ConversationRequest

router = APIRouter(prefix="/booking", tags=["Specialist: Booking Service"])

@router.post("/handle_conversation", name="Handle Booking Conversation")
async def handle_conversation(request: ConversationRequest):
    print(f"\n--- [BOOKING_SERVICE] Activated with context: {request.shared_context} ---")
    # In the future, this agent would call a booking API.
    # For now, it just completes its step and updates the context.
    updated_context = request.shared_context
    updated_context['booking_confirmation'] = "BK-12345"
    
    return {
        "status": "completed",
        "updated_context": updated_context,
        "display_message": {"response_type": "answer", "text": "I have successfully booked a table for you!"}
    }