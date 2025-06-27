# backend/services/executor_service/main.py
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
    goal: Optional[str] = None


router = APIRouter(prefix="/executor", tags=["Executor Agent"])


# --- EXECUTOR AGENT CONSTITUTION V1 ---
EXECUTOR_AGENT_CONSTITUTION_PROMPT = """
You are a diligent and resourceful AI Executor. Your sole purpose is to complete a single, specific task that is part of a larger plan.

**--- YOUR DIRECTIVE ---**
1.  **Understand Your Task:** Your goal for this turn is provided below. It is a single step from a plan created by a Planner AI.
2.  **Use Your Tools:** Your primary tool is Google Search. If your task requires real-world, up-to-date information (like finding restaurants, checking availability, or getting reviews), you MUST use the `Google Search` tool.
3.  **Engage the User When Necessary:** If you cannot complete your task without a decision from the user, you MUST ask a clear question and provide options.
4.  **Report Your Results:** When you have completed your task, provide a concise summary of the result. If you found information, present it clearly. If you are asking a question, make sure it is easy to understand.

**--- OUTPUT FORMATS (Choose ONE) ---**

* **To Use Google Search:**
    `{{"response_type": "tool_use", "tool_name": "Google Search", "tool_input": {{"query": "your precise search query"}}}}`

* **To Ask the User a Question:**
    `{{"response_type": "clarification", "text": "Your clear question to the user?", "options": ["Option 1", "Option 2"]}}`

* **To Present Final Results in a Widget:**
    `{{"response_type": "canvas", "widgets": [{{"widget_type": "list", "title": "Results of my task:", "items": ["Result 1", "Result 2"]}}], "text": "Here is what I found. What would you like to do next?"}}`

* **To Give a Simple Answer:**
    `{{"response_type": "answer", "text": "I have completed the task. [Your summary here]."}}`

**--- YOUR GOAL FOR THIS TURN ---**
{goal}

**--- SHARED CONTEXT FROM PREVIOUS STEPS ---**
{shared_context}

**--- FULL CONVERSATION HISTORY ---**
{full_conversation_history}
"""

@router.post("/execute_step")
async def execute_step(request: ConversationRequest):
    print("\n--- [EXECUTOR] Executor Agent Activated ---")
    print(f"--- [EXECUTOR] Received Goal: {request.goal} ---")

    model = genai.GenerativeModel(
        'gemini-1.5-flash',
        generation_config={"response_mime_type": "application/json"}
    )
    
    full_history_string = "\n".join([f"{msg.sender.capitalize()}: {msg.text}" for msg in request.messages if msg.text])

    prompt = EXECUTOR_AGENT_CONSTITUTION_PROMPT.format(
        goal=request.goal,
        shared_context=json.dumps(request.shared_context),
        full_conversation_history=full_history_string
    )
    
    try:
        response = model.generate_content(prompt)
        parsed_json = json.loads(response.text)
        print(f"--- [EXECUTOR] Parsed AI Response: {parsed_json} ---")

        # The Executor always hands control back, so its own status is less critical.
        # We determine the final status in the orchestrator.
        return {
            "status": "completed_step",
            "display_message": parsed_json
        }

    except Exception as e:
        print(f"--- [EXECUTOR] CRITICAL ERROR: {e} ---")
        return {
            "status": "error",
            "display_message": {
                "response_type": "answer",
                "text": "I encountered a problem trying to execute that step. Please try again."
            }
        }