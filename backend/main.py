# backend/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
from typing import Dict, Any, List
import json
from datetime import datetime
import pytz

# Import the new Planner and Executor services
from services.reasoning_service.main import ConversationRequest
from services.reasoning_service.main import router as planner_router
from services.executor_service.main import router as executor_router

# The tooling service is no longer needed here
# from services.tooling_service.main import perform_Google Search

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

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
    Orchestrates the Planner-Executor model with user consent at each step.
    """
    print("\n\n--- [ORCHESTRATOR] New Conversation Turn ---")
    current_context = request.shared_context.copy()
    user_latest_message = request.messages[-1].text if request.messages else ""

    if not request.messages or 'user_location' not in current_context:
        # ... (grounding logic is the same)
        ist = pytz.timezone('Asia/Kolkata')
        current_time = datetime.now(ist)
        current_context['user_location'] = "Hyderabad, Telangana, India"
        current_context['current_time'] = current_time.strftime("%A, %B %d, %Y at %I:%M %p IST")
        print(f"--- [ORCHESTRATOR] New conversation started. Grounding with reality. ---")

    async with httpx.AsyncClient() as client:
        try:
            # Case 1: User has given permission to execute the next step.
            if user_latest_message == "Yes, proceed." and "pending_plan" in current_context:
                plan = current_context.get("pending_plan", [])
                if not plan:
                    return {"agent_response": {"response_type": "answer", "text": "The plan is complete."}, "shared_context": current_context}

                step_to_execute = plan[0]
                remaining_plan = plan[1:]
                
                print(f"\n--- [ORCHESTRATOR] User consented. Executing step: '{step_to_execute}' ---")
                
                executor_payload = {"messages": [msg.model_dump() for msg in request.messages], "shared_context": current_context, "goal": step_to_execute}
                executor_response = await call_agent("executor_service", executor_payload, client)
                
                display_message = executor_response.get("display_message")
                
                # After execution, ask for permission for the next step, if one exists.
                if remaining_plan:
                    current_context["pending_plan"] = remaining_plan
                    permission_text = f"The previous step is complete. The next step is to '{remaining_plan[0]}'. Shall I proceed?"
                    display_message = {"response_type": "clarification", "text": permission_text, "options": ["Yes, proceed.", "No, stop."]}
                else:
                    # The plan is finished. The final message from the executor is what will be shown.
                    print("--- [ORCHESTRATOR] Final step of plan completed. ---")
                    current_context.pop("pending_plan", None)
                
                return {"agent_response": display_message, "shared_context": current_context}

            # Case 2: No pending plan, so call the Planner.
            else:
                planner_payload = request.model_dump()
                planner_payload['shared_context'] = current_context
                planner_response = await call_agent("planner_service", planner_payload, client)

                if planner_response.get("response_type") == "plan_generated":
                    plan = planner_response.get("plan", [])
                    if plan:
                        current_context["pending_plan"] = plan
                        permission_text = f"I have created a plan to achieve your goal. The first step is to '{plan[0]}'. Shall I proceed?"
                        planner_response = {"response_type": "clarification", "text": permission_text, "options": ["Yes, proceed.", "No, stop."]}
                
                return {"agent_response": planner_response, "shared_context": current_context}
        
        except Exception as e:
            print(f"--- [ORCHESTRATOR] CRITICAL ERROR: {e} ---")
            raise HTTPException(status_code=500, detail=str(e))


# Include ONLY the new routers
app.include_router(planner_router)
app.include_router(executor_router)

# The user profile service is still useful for context
app.include_router(user_profile_service.router)


@app.get("/")
def read_root():
    return {"message": "Agentive Pro (Planner-Executor Model) is running."}