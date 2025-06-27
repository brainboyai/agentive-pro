# backend/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
from typing import Dict, Any, List
import json
from datetime import datetime
import pytz

# Import the new Planner and Executor services
from services.reasoning_service.main import ConversationRequest # Using the same model
from services.reasoning_service.main import router as planner_router
from services.executor_service.main import router as executor_router

# Import only the necessary tools
from services.tooling_service.main import perform_google_search

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# --- NEW, SIMPLIFIED AGENT ENDPOINTS ---
AGENT_ENDPOINTS = {
    "planner_service": "http://127.0.0.1:8000/planner/get_plan",
    "executor_service": "http://127.0.0.1:8000/executor/execute_step",
}

async def call_agent(agent_name: str, payload: Dict, client: httpx.AsyncClient) -> Dict[str, Any]:
    """Generic function to call any agent service."""
    endpoint = AGENT_ENDPOINTS.get(agent_name)
    if not endpoint:
        return {"response_type": "answer", "text": f"Error: The requested agent '{agent_name}' is not available."}
    
    response = await client.post(endpoint, json=payload, timeout=60.0)
    response.raise_for_status()
    return response.json()


@app.post("/api/v1/conversation")
async def orchestrate_conversation(request: ConversationRequest):
    """
    This is the main endpoint that orchestrates the entire conversation.
    It manages the Planner-Executor model with user consent at each step.
    """
    print("\n\n--- [ORCHESTRATOR] New Conversation Turn ---")
    current_context = request.shared_context.copy()
    user_latest_message = request.messages[-1].text if request.messages else ""

    # Ground the conversation with reality on the very first turn
    if not request.messages or 'user_location' not in current_context:
        ist = pytz.timezone('Asia/Kolkata')
        current_time = datetime.now(ist)
        current_context['user_location'] = "Hyderabad, Telangana, India"
        current_context['current_time'] = current_time.strftime("%A, %B %d, %Y at %I:%M %p IST")
        print(f"--- [ORCHESTRATOR] New conversation started. Grounding with reality. ---")

    async with httpx.AsyncClient() as client:
        try:
            # --- CORE ORCHESTRATION LOGIC ---

            # Case 1: User has given consent to execute the next step of a plan.
            if user_latest_message == "Yes, proceed." and "pending_plan" in current_context:
                plan = current_context.get("pending_plan", [])
                
                if not plan:
                    return {"agent_response": {"response_type": "answer", "text": "There is no plan to execute."}, "shared_context": current_context}

                # Execute the next step
                step_to_execute = plan[0]
                remaining_plan = plan[1:]
                
                print(f"\n--- [ORCHESTRATOR] User consented. Executing step: '{step_to_execute}' ---")
                
                executor_payload = {"messages": [msg.model_dump() for msg in request.messages], "shared_context": current_context, "goal": step_to_execute}
                executor_response = await call_agent("executor_service", executor_payload, client)
                
                display_message = executor_response.get("display_message")
                
                # After execution, check if there are more steps in the plan
                if remaining_plan:
                    current_context["pending_plan"] = remaining_plan
                    next_step_text = remaining_plan[0]
                    permission_text = f"The previous step is complete. The next step is to '{next_step_text}'. Shall I proceed?"
                    display_message = {"response_type": "clarification", "text": permission_text, "options": ["Yes, proceed.", "No, stop."]}
                else:
                    # This was the last step, the plan is complete.
                    print("--- [ORCHESTRATOR] Final step of plan completed. ---")
                    current_context.pop("pending_plan", None)
                    # The final message from the executor is shown
                
                return {"agent_response": display_message, "shared_context": current_context}

            # Case 2: No pending plan, so we call the Planner to see what to do next.
            else:
                planner_payload = request.model_dump()
                planner_payload['shared_context'] = current_context
                planner_response = await call_agent("planner_service", planner_payload, client)

                # If the Planner generated a new plan, save it and ask for permission to start.
                if planner_response.get("response_type") == "plan_generated":
                    plan = planner_response.get("plan", [])
                    if plan:
                        current_context["pending_plan"] = plan
                        first_step_text = plan[0]
                        permission_text = f"I have created a plan to achieve your goal. The first step is to '{first_step_text}'. Shall I proceed?"
                        planner_response = {"response_type": "clarification", "text": permission_text, "options": ["Yes, proceed.", "No, stop."]}
                
                return {"agent_response": planner_response, "shared_context": current_context}
        
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                 error_message = "I'm currently experiencing a high volume of requests. Please try again in a moment."
                 return {"agent_response": {"response_type": "answer", "text": error_message}, "shared_context": current_context}
            raise HTTPException(status_code=e.response.status_code, detail=f"Error calling agent service: {e.response.text}")
        except Exception as e:
            print(f"--- [ORCHESTRATOR] CRITICAL ERROR: {e} ---")
            raise HTTPException(status_code=500, detail=str(e))

# --- Include the NEW routers ---
app.include_router(planner_router)
app.include_router(executor_router)

# --- The old specialist routers are no longer needed ---
# app.include_router(food_router)
# app.include_router(booking_router)
# app.include_router(travel_router)
# etc...

@app.get("/")
def read_root():
    return {"message": "Agentive Pro (Planner-Executor Model) is running."}