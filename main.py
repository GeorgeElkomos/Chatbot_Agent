"""
File: main.py (relative to Chatbot_Agent)
"""
import sys
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from remove_emoji import remove_emoji
from orchestrator import orchestrate
from agents.registry.registration import register_agents
from agents.llm_config.utils import get_api_usage_stats, reset_api_usage_stats
from typing import Dict, Any
from pydantic import BaseModel

class ChatbotRequest(BaseModel):
    user_input: str

class ChatbotResponse(BaseModel):
    status: str
    response: Dict[str, Any]
    message: str = None

class HealthResponse(BaseModel):
    status: str
    message: str

class APIUsageResponse(BaseModel):
    status: str
    usage_stats: Dict[str, Any]

app = FastAPI(title="Chatbot API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

remove_emoji()
register_agents()

# FastAPI Endpoints
@app.post("/chatbot/public", response_model=ChatbotResponse)
async def chatbot_endpoint(request: ChatbotRequest):
    try:
        if not request.user_input.strip():
            raise HTTPException(status_code=400, detail="user_input cannot be empty")
        final_outputs = orchestrate(request.user_input, logs=False)
        return ChatbotResponse(
            status="success",
            response=final_outputs,
            message="Request processed successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="healthy",
        message="Chatbot API is running successfully"
    )

@app.get("/api/usage", response_model=APIUsageResponse)
async def get_api_usage():
    """Get API usage statistics"""
    try:
        stats = get_api_usage_stats()
        return APIUsageResponse(
            status="success",
            usage_stats=stats
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving usage stats: {str(e)}")

@app.post("/api/usage/reset")
async def reset_usage_stats():
    """Reset API usage statistics"""
    try:
        reset_api_usage_stats()
        return {"status": "success", "message": "API usage statistics reset successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error resetting usage stats: {str(e)}")

# Run the FastAPI server with uvicorn
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--server":
        uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
    else:
        _user_request = "summarize the Last transfer."
        print("User Input:", _user_request)
        response = orchestrate(_user_request, logs=False)
        print("Final outputs:", response)