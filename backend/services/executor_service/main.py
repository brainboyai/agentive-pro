# backend/services/executor_service/main.py
import os
import json
from fastapi import APIRouter
import google.generativeai as genai
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from dotenv import load_dotenv

# --- The Executor now imports the search tool directly ---
from ..tooling_service.main import perform_google_search

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

# --- EXECUTOR AGENT CONSTITUTION V2 (Self-Sufficient) ---
EXECUTOR_AGENT_CONSTITUTION_PROMPT = """
You are a diligent and resourceful AI Executor. Your sole purpose is to complete a single, specific task. You have direct access to a Google Search tool.

**--- YOUR DIRECTIVE ---**
1.  **Understand Your Task:** Your goal is provided below.
2.  **Decide if a Tool is Needed:** Analyze your task. If it requires any real-world, up-to-date information, you MUST decide to use your `Google Search` tool.
3.  **Formulate a Response:** Based on your decision, generate ONE of the following JSON outputs.

**--- OUTPUT FORMATS (Choose ONE) ---**

* **If you need to use Google Search:**
    `{{"response_type": "tool_use", "tool_name": "Google Search", "tool_input": {{"query": "your precise search query"}}}}`

* **If you need a decision from the user:**
    `{{"response_type": "clarification", "text": "Your clear question to the user?", "options": ["Option 1", "Option 2"]}}`
    
* **If you have completed your task and have a final answer:**
    `{{"response_type": "answer", "text": "I have completed the task. [Your concise summary here]."}}`
"""

@router.post("/execute_step")
async def execute_step(request: ConversationRequest):
    print("\n--- [EXECUTOR] Executor Agent Activated ---")
    print(f"--- [EXECUTOR] Received Goal: {request.goal} ---")

    model = genai.GenerativeModel('gemini-1.5-flash', generation_config={"response_mime_type": "application/json"})
    
    full_history_string = "\n".join([f"{msg.sender.capitalize()}: {msg.text}" for msg in request.messages if msg.text])

    prompt = EXECUTOR_AGENT_CONSTITUTION_PROMPT.format(
        goal=request.goal,
        shared_context=json.dumps(request.shared_context),
        full_conversation_history=full_history_string
    )
    
    try:
        # First call to the AI to decide what to do
        initial_response = model.generate_content(prompt)
        parsed_response = json.loads(initial_response.text)
        print(f"--- [EXECUTOR] Initial Decision: {parsed_response} ---")

        # If the AI decides to use a tool, execute it here.
        if parsed_response.get("response_type") == "tool_use":
            print(f"--- [EXECUTOR] Decided to use a tool: {parsed_response.get('tool_name')} ---")
            query = parsed_response["tool_input"]["query"]
            tool_result = perform_google_search(query)
            
            # Second call to the AI to analyze the tool results
            new_prompt = f"""
            You are an AI Executor. You just performed a Google Search for the query: '{query}'.
            The result of the search is:
            {json.dumps(tool_result)}

            Your task now is to analyze this result and present a final answer to the user in a clear and concise way. 
            If the results are good, present them. If they are bad, state that you could not find the information.
            Your output MUST be a single JSON object with `response_type` of `answer` or `canvas`.
            Example: `{{"response_type": "answer", "text": "Based on my search, I found..."}}`
            """
            final_response = model.generate_content(new_prompt)
            parsed_response = json.loads(final_response.text)
            print(f"--- [EXECUTOR] Final response after tool use: {parsed_response} ---")

        return {"status": "completed_step", "display_message": parsed_response}

    except Exception as e:
        print(f"--- [EXECUTOR] CRITICAL ERROR: {e} ---")
        return {"status": "error", "display_message": {"response_type": "answer", "text": "I encountered a problem executing that step."}}