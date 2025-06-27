# backend/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
from typing import Dict, Any

from services.reasoning_service.main import ConversationRequest
from services.reasoning_service.main import router as planner_router
from services.user_profile_service.main import router as user_profile_service

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

AGENT_ENDPOINTS = {
    "planning_service": "http://127.0.0.1:8000/planner/generate_plan",
}

async def call_agent(agent_name: str, payload: Dict, client: httpx.AsyncClient) -> Dict[str, Any]:
    endpoint = AGENT_ENDPOINTS.get(agent_name)
    if not endpoint:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found.")
    
    response = await client.post(endpoint, json=payload, timeout=60.0)
    response.raise_for_status()
    return response.json()

@app.post("/api/v1/conversation")
async def orchestrate_conversation(request: ConversationRequest):
    print("\n\n--- [ORCHESTRATOR] New Request ---")
    
    async with httpx.AsyncClient() as client:
        try:
            print("--- [ORCHESTRATOR] Calling Planner Agent ---")
            planner_response = await call_agent("planning_service", request.model_dump(), client)
            return {"agent_response": planner_response}
        
        except Exception as e:
            print(f"--- [ORCHESTRATOR] CRITICAL ERROR: {e} ---")
            raise HTTPException(status_code=500, detail=str(e))

# Include only the necessary routers
app.include_router(planner_router)
app.include_router(user_profile_service)

@app.get("/")
def read_root():
    return {"message": "Agentive Pro (Simple Planner) is running."}