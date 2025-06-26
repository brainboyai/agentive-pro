# backend/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
from typing import Dict, Any
import json 

# Import all models and routers
from services.reasoning_service.main import ConversationRequest
from services.reasoning_service.main import router as reasoning_router
from services.user_profile_service.main import router as user_profile_router
from services.food_service.main import router as food_router
from services.booking_service.main import router as booking_router
from services.travel_service.main import router as travel_router
from services.calendar_service.main import router as calendar_router
from services.discovery_service.main import router as discovery_router
from services.tooling_service.main import perform_google_search # Import the search tool

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# The expanded list of all available agents
AGENT_ENDPOINTS = {
    "reasoning_service": "http://127.0.0.1:8000/reasoning/handle_conversation",
    "food_service": "http://127.0.0.1:8000/food/handle_conversation",
    "booking_service": "http://127.0.0.1:8000/booking/handle_conversation",
    "travel_service": "http://127.0.0.1:8000/travel/handle_conversation",
    "calendar_service": "http://127.0.0.1:8000/calendar/handle_conversation",
    "discovery_service": "http://127.0.0.1:8000/discovery/handle_conversation",
}

async def call_agent(agent_name: str, payload: Dict, client: httpx.AsyncClient) -> Dict[str, Any]:
    # ... (this helper function remains the same as the last version)
    endpoint = AGENT_ENDPOINTS.get(agent_name)
    if not endpoint:
        # ... (graceful handling of unknown agents)
        return {"status": "completed", "display_message": {"response_type": "answer", "text": "Sorry, a required tool is not available."}}
    response = await client.post(endpoint, json=payload, timeout=60.0)
    response.raise_for_status()
    return response.json()

# In backend/main.py

@app.post("/api/v1/conversation")
async def orchestrate_conversation(request: ConversationRequest):
    print("\n\n--- [ORCHESTRATOR] New Conversation Turn ---")
    current_context = request.shared_context.copy()
    print(f"--- [ORCHESTRATOR] Initial Context for this turn: {current_context} ---")

    async with httpx.AsyncClient() as client:
        try:
            # Create the initial payload, ensuring all Pydantic models are converted to dicts
            initial_payload = request.model_dump()
            
            # 1. Always start by calling the Manager Agent to get a plan or direct response
            agent_response = await call_agent("reasoning_service", initial_payload, client)

            # --- BRANCH 1: Handle Tool Use requested by the Manager ---
            if agent_response.get("response_type") == "tool_use":
                print(f"--- [ORCHESTRATOR] Manager Agent requested tool: {agent_response.get('tool_name')} ---")
                tool_name = agent_response.get("tool_name")
                tool_input = agent_response.get("tool_input", {})
                
                tool_result = None
                if tool_name == "Google Search":
                    tool_result = perform_google_search(tool_input.get("query"))
                else:
                    raise HTTPException(status_code=400, detail=f"Unknown tool requested: {tool_name}")

                print("--- [ORCHESTRATOR] Sending tool result back to Manager for analysis ---")
                
                # We add the tool result to the conversation history for context
                tool_result_message = {
                    "sender": "system",
                    "text": f"Tool Result for '{tool_name}':\n{json.dumps(tool_result)}"
                }
                
                # Create a mutable list of message dictionaries
                messages_for_recall = [msg.model_dump() for msg in request.messages]
                messages_for_recall.append(tool_result_message)
                
                # Create a new payload for the second call
                new_payload = {
                    "messages": messages_for_recall,
                    "shared_context": current_context
                }

                # Re-call the manager with the new context
                final_response = await call_agent("reasoning_service", new_payload, client)
                return {"agent_response": final_response, "shared_context": current_context}
            
            # --- BRANCH 2: Handle Workflow Execution ---
            elif agent_response.get("response_type") == "execute_workflow":
                workflow_steps = agent_response.get("steps", [])
                print(f"--- [ORCHESTRATOR] Starting workflow with {len(workflow_steps)} steps. ---")
                
                final_display_message = None
                
                # Loop through the steps and execute them sequentially
                for i, step in enumerate(workflow_steps):
                    agent_to_call = step if isinstance(step, str) else step.get("agent")
                    if not agent_to_call:
                        print(f"--- [ORCHESTRATOR] WARNING: Could not determine agent for step {i+1}. Skipping. ---")
                        continue

                    print(f"\n--- [ORCHESTRATOR] Executing Step {i+1}: Calling '{agent_to_call}' ---")
                    
                    # Create the payload for this specific step, ensuring context is up-to-date
                    step_payload = {
                        "messages": [msg.model_dump() for msg in request.messages],
                        "shared_context": current_context
                    }
                    
                    specialist_response = await call_agent(agent_to_call, step_payload, client)

                    # --- Nested Logic: Handle Tool Use requested by a SPECIALIST ---
                    display_message = specialist_response.get("display_message", {})
                    if display_message and display_message.get("response_type") == "tool_use":
                        tool_info = display_message
                        print(f"--- [ORCHESTRATOR] SPECIALIST '{agent_to_call}' requested tool: {tool_info['tool_name']} ---")
                        
                        tool_result = perform_google_search(tool_info["tool_input"].get("query"))
                        
                        # Add the tool result to the conversation history
                        tool_result_message = {"sender": "system", "text": f"Tool Result for '{tool_info['tool_name']}':\n{json.dumps(tool_result)}"}
                        # Create a mutable list of message dicts from the original request
                        messages_for_recall = [msg.model_dump() for msg in request.messages]
                        messages_for_recall.append(tool_result_message)
                        
                        print(f"--- [ORCHESTRATOR] Sending tool result back to '{agent_to_call}' for analysis ---")
                        new_specialist_payload = {"messages": messages_for_recall, "shared_context": current_context}
                        
                        # Re-call the SAME specialist with the new information
                        specialist_response = await call_agent(agent_to_call, new_specialist_payload, client)
                    # --- End of Nested Tool Use Logic ---

                    if "updated_context" in specialist_response:
                        current_context.update(specialist_response.get("updated_context", {}))
                        print(f"--- [ORCHESTRATOR] Context updated to: {current_context} ---")
                    
                    final_display_message = specialist_response.get("display_message")

                    if specialist_response.get("status") != "completed":
                        print("--- [ORCHESTRATOR] Workflow paused, awaiting user input. ---")
                        break
                
                print("--- [ORCHESTRATOR] Workflow finished for this turn. ---")
                return {"agent_response": final_display_message, "shared_context": current_context}

            # --- BRANCH 3: Handle Direct Response from Manager ---
            else:
                print("--- [ORCHESTRATOR] Manager handled directly. ---")
                return {"agent_response": agent_response, "shared_context": current_context}

        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=f"Error calling agent service: {e.response.text}")
        except Exception as e:
            print(f"--- [ORCHESTRATOR] CRITICAL ERROR: {e} ---")
            raise HTTPException(status_code=500, detail=str(e))
# Include all the new routers
# --- FIX: Include all the new routers ---
app.include_router(reasoning_router)
app.include_router(user_profile_router)
app.include_router(food_router)
app.include_router(booking_router)
app.include_router(travel_router)
app.include_router(calendar_router)
app.include_router(discovery_router)

@app.get("/")
def read_root():
    return {"message": "Agentive Pro Workflow & Search Engine is running."}